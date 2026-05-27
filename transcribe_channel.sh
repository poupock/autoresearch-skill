#!/usr/bin/env bash
#
# transcribe_channel.sh — download YouTube captions for a channel's recent
# uploads (videos + live streams) and turn them into clean plain-text transcripts.
#
# Why run it locally? YouTube IP-blocks data-center / cloud IPs ("Sign in to
# confirm you're not a bot" / HTTP 429). On a normal home connection it just works.
#
# USAGE
#   bash transcribe_channel.sh                         # default channel, last 3 months
#   bash transcribe_channel.sh "https://www.youtube.com/@stori3.14"
#
# OPTIONS (env vars)
#   MONTHS=3                 how many months back to go               (default 3)
#   SUB_LANGS="en.*"         caption languages, regex; "all" for everything
#   OUTDIR=transcripts       where output goes
#   CLEAN_ONLY=1             skip downloading, only (re)build .txt from _raw
#   YT_COOKIES_BROWSER=chrome   use browser cookies if you ever hit a bot check
#   YT_COOKIES_FILE=cookies.txt same, from an exported cookies.txt
#
# OUTPUT
#   transcripts/videos/<date>-<title>-<id>.txt      clean transcript
#   transcripts/streams/<date>-<title>-<id>.txt
#   transcripts/{videos,streams}/listing.tsv        date / duration / id / title
#   transcripts/{videos,streams}/_raw/*.vtt         original caption files
#
set -euo pipefail

CHANNEL="${1:-https://www.youtube.com/@stori3.14}"
CHANNEL="${CHANNEL%/}"
MONTHS="${MONTHS:-3}"
SUB_LANGS="${SUB_LANGS:-en.*}"
OUTDIR="${OUTDIR:-transcripts}"

# cutoff = MONTHS calendar months before today, as YYYYMMDD (portable)
SINCE="$(python3 - "$MONTHS" <<'PY'
import sys, datetime, calendar
m = int(sys.argv[1]); d = datetime.date.today()
month = d.month - m; year = d.year
while month <= 0:
    month += 12; year -= 1
day = min(d.day, calendar.monthrange(year, month)[1])
print(datetime.date(year, month, day).strftime("%Y%m%d"))
PY
)"

echo "Channel : $CHANNEL"
echo "Window  : uploads on/after $SINCE (last $MONTHS months)"
echo "Captions: $SUB_LANGS"
echo "Output  : $OUTDIR/"
echo

clean_stage () {
  OUTDIR="$OUTDIR" python3 - <<'PY'
import os, re, glob, html
OUT = os.environ["OUTDIR"]
TAG = re.compile(r"<[^>]+>")
LANG_PRIORITY = ["en", "en-US", "en-GB", "en-orig"]

def clean_vtt(path):
    # 1) keep only spoken-text lines, strip tags/entities, drop exact repeats
    lines, last = [], None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip():
                continue
            if line.startswith(("WEBVTT", "Kind:", "Language:", "NOTE", "STYLE", "Region:")):
                continue
            if "-->" in line or re.match(r"^\d+$", line):
                continue
            text = html.unescape(TAG.sub("", line)).strip()
            if not text or text == last:
                continue
            lines.append(text); last = text
    # 2) merge YouTube's rolling captions: drop the word-overlap between the
    #    tail of what we have and the head of the next line
    words = []
    for line in lines:
        nw = line.split()
        o = 0
        for k in range(min(len(words), len(nw)), 0, -1):
            if words[-k:] == nw[:k]:
                o = k; break
        words += nw[o:]
    return words

def lang_of(f):
    m = re.search(r"\.([A-Za-z0-9_-]+)\.vtt$", f)
    return m.group(1) if m else ""

def base_of(fname):
    m = re.match(r"(.*)\.[A-Za-z0-9_-]+\.vtt$", fname)
    return m.group(1) if m else fname[:-4]

for tab in ("videos", "streams"):
    raw = os.path.join(OUT, tab, "_raw")
    if not os.path.isdir(raw):
        continue
    groups = {}
    for v in glob.glob(os.path.join(raw, "*.vtt")):
        groups.setdefault(base_of(os.path.basename(v)), []).append(v)
    n = 0
    for base, files in sorted(groups.items()):
        files.sort(key=lambda f: (LANG_PRIORITY.index(lang_of(f))
                                   if lang_of(f) in LANG_PRIORITY else 99, lang_of(f)))
        lines = clean_vtt(files[0])
        if not lines:
            continue
        text = re.sub(r"\s+", " ", " ".join(lines)).strip()
        with open(os.path.join(OUT, tab, base + ".txt"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
        n += 1
    print(f"  {tab}: {n} transcript(s) written")
PY
}

if [ "${CLEAN_ONLY:-}" = "1" ]; then
  echo "CLEAN_ONLY=1 -> rebuilding transcripts from existing _raw captions"
  clean_stage
  echo "Done."
  exit 0
fi

# ── ensure yt-dlp ────────────────────────────────────────────────────────────
if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "Installing yt-dlp..."
  python3 -m pip install -q --upgrade yt-dlp
fi
echo "Tip: installing a JS runtime (deno) improves YouTube extraction reliability:"
echo "     https://github.com/yt-dlp/yt-dlp/wiki/EJS"
echo

AUTH=()
[ -n "${YT_COOKIES_BROWSER:-}" ] && AUTH+=(--cookies-from-browser "$YT_COOKIES_BROWSER")
[ -n "${YT_COOKIES_FILE:-}" ]    && AUTH+=(--cookies "$YT_COOKIES_FILE")

fetch_tab () {  # $1 = videos | streams
  local tab="$1"
  local raw="$OUTDIR/$tab/_raw"
  mkdir -p "$raw"
  rm -f "$OUTDIR/$tab/listing.tsv"
  echo "=== '$tab': downloading captions (newest first, stop once older than $SINCE) ==="
  yt-dlp \
    "${AUTH[@]}" \
    --ignore-errors --no-warnings \
    --dateafter "$SINCE" --break-on-reject --break-per-input \
    --skip-download \
    --write-auto-subs --write-subs --sub-langs "$SUB_LANGS" --sub-format "vtt/best" \
    --restrict-filenames \
    --sleep-requests 1 --retries 5 --fragment-retries 5 \
    --print-to-file "%(upload_date)s	%(duration)s	%(id)s	%(title)s" "$OUTDIR/$tab/listing.tsv" \
    -o "$raw/%(upload_date)s-%(title)s-%(id)s.%(ext)s" \
    "$CHANNEL/$tab" || true
  echo
}

fetch_tab videos
fetch_tab streams

echo "=== Converting captions to clean text ==="
clean_stage

echo
echo "Done. Transcripts are in: $OUTDIR/{videos,streams}/*.txt"
echo "Item lists (date / duration / id / title): $OUTDIR/{videos,streams}/listing.tsv"
