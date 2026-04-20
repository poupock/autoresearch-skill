"""
News monitor for AADS/MAADS/Slise/Welldone content pipeline.

Fetches daily crypto digests from cryptointegrat.com and The Block,
filters by project keywords, and returns ranked recommendations
matched to the upcoming content calendar dates.
"""

import json
import re
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from typing import Optional


# ---------------------------------------------------------------------------
# Project keyword config
# ---------------------------------------------------------------------------

PROJECT_KEYWORDS: dict[str, list[str]] = {
    "AADS": [
        "crypto ad", "bitcoin ad", "crypto advertising", "ad network",
        "cpm", "cpc", "igaming ad", "crypto casino ad", "ad ban",
        "google crypto", "meta crypto", "twitter crypto ads", "x ads",
        "ad restriction", "crypto publisher", "affiliate ban",
        "banner ad", "display ad", "programmatic crypto",
    ],
    "MAADS": [
        "clarity act", "genius act", "crypto regulation", "sec crypto",
        "cftc crypto", "igaming regulation", "gambling ban", "gambling ad",
        "draftkings", "fanduel", "betmgm", "crypto marketing",
        "user acquisition", "crypto cac", "marketing budget",
        "world cup gambling", "fifa gambling", "australia crypto",
        "afsl", "dao legal", "dao personhood", "crypto compliance",
        "tether adoption", "stablecoin payments", "mastercard crypto",
        "polymarket", "etoro", "zengo",
    ],
    "Slise": [
        "etherscan", "dextools", "dapp advertising", "onchain targeting",
        "wallet targeting", "dex", "defi advertising", "solscan",
        "birdeye", "geckoterminal", "blockchain explorer ad",
        "dapp session", "wallet analytics", "onchain data",
        "web3 targeting", "context targeting",
    ],
    "Welldone": [
        "smart contract security", "ai code vulnerability", "eu ai act",
        "fintech compliance", "web3 security", "dao exploit",
        "blind signing", "security audit", "veracode", "certik",
        "glamsterdam", "ethereum upgrade", "epbs", "stride",
        "ai generated code", "llm security",
    ],
}

# How many days ahead to look when matching to the content calendar
LOOKAHEAD_DAYS = 14


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class NewsItem:
    title: str
    summary: str
    source: str
    url: str
    published: Optional[date] = None
    matched_projects: list[str] = field(default_factory=list)
    relevance_score: int = 0
    post_angle: str = ""


# ---------------------------------------------------------------------------
# HTML parser — strips tags, returns plain text
# ---------------------------------------------------------------------------

class _StripHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []

    def handle_data(self, data: str):
        self._chunks.append(data)

    def get_text(self) -> str:
        return " ".join(self._chunks)


def _strip_html(raw: str) -> str:
    p = _StripHTML()
    p.feed(raw)
    return re.sub(r"\s+", " ", p.get_text()).strip()


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NewsMonitor/1.0; +https://maads.com)"
    )
}


def _fetch(url: str, timeout: int = 10) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} fetching {url}") from e
    except Exception as e:
        raise RuntimeError(f"Failed fetching {url}: {e}") from e


# ---------------------------------------------------------------------------
# Parsers for each source
# ---------------------------------------------------------------------------

def _parse_cryptointegrat(html: str, source_url: str) -> list[NewsItem]:
    """Extract news bullets from Crypto Integrated digest pages."""
    text = _strip_html(html)
    items: list[NewsItem] = []

    # Each bullet typically starts with a company name or emoji/dash
    # Split on newline-like separators (after stripping HTML they appear as spaces)
    # Use a heuristic: sentences that start with a capital company name
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\$€£0-9])", text)

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 40 or len(sentence) > 600:
            continue
        # Skip navigation / boilerplate
        if any(skip in sentence.lower() for skip in [
            "subscribe", "unsubscribe", "click here", "privacy policy",
            "terms of", "follow us", "newsletter",
        ]):
            continue
        items.append(NewsItem(
            title=sentence[:120].rstrip(".") + ("…" if len(sentence) > 120 else ""),
            summary=sentence,
            source="Crypto Integrated",
            url=source_url,
        ))

    return items


def _parse_theblock(html: str, source_url: str) -> list[NewsItem]:
    """Extract article titles from The Block's news page."""
    items: list[NewsItem] = []
    # Article titles are in <h3> or <h2> tags
    for tag in ("h3", "h2"):
        for match in re.finditer(
            rf"<{tag}[^>]*>(.*?)</{tag}>", html, re.DOTALL | re.IGNORECASE
        ):
            title = _strip_html(match.group(1)).strip()
            if len(title) < 20 or len(title) > 200:
                continue
            if any(skip in title.lower() for skip in [
                "the block", "subscribe", "sign in", "log in"
            ]):
                continue
            items.append(NewsItem(
                title=title,
                summary=title,
                source="The Block",
                url=source_url,
            ))

    return items


# ---------------------------------------------------------------------------
# Scoring & filtering
# ---------------------------------------------------------------------------

def _score_item(item: NewsItem) -> NewsItem:
    """Score relevance, set matched projects and suggested post angle."""
    text_lower = (item.title + " " + item.summary).lower()
    matched: dict[str, int] = {}

    for project, keywords in PROJECT_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits:
            matched[project] = hits

    if not matched:
        return item

    item.matched_projects = sorted(matched, key=matched.get, reverse=True)  # type: ignore[arg-type]
    item.relevance_score = sum(matched.values())

    # Generate a quick post angle suggestion
    top = item.matched_projects[0]
    if top == "AADS":
        item.post_angle = "Market Insight: competitor restrictions → AADS advantage"
    elif top == "MAADS":
        item.post_angle = "Hot take / Regulatory news → marketing window angle"
    elif top == "Slise":
        item.post_angle = "Market Insight: dApp session context → Slise placement"
    elif top == "Welldone":
        item.post_angle = "Hot take: security/compliance → Welldone expertise"

    return item


# ---------------------------------------------------------------------------
# Main fetching functions
# ---------------------------------------------------------------------------

def fetch_cryptointegrat(
    days_back: int = 2,
) -> list[NewsItem]:
    """Fetch recent Crypto Integrated digests and parse news items."""
    items: list[NewsItem] = []
    today = date.today()

    for delta in range(days_back + 1):
        target = today - timedelta(days=delta)
        date_str = target.strftime("%B-%-d").lower()  # e.g. "april-19"
        url = f"https://www.cryptointegrat.com/p/crypto-news-{date_str}-2026"

        try:
            html = _fetch(url)
            parsed = _parse_cryptointegrat(html, url)
            for item in parsed:
                item.published = target
            items.extend(parsed)
            time.sleep(0.5)
        except RuntimeError:
            # Date may not have a digest (weekend, holiday) — skip silently
            pass

    return items


def fetch_theblock() -> list[NewsItem]:
    """Fetch latest headlines from The Block."""
    url = "https://www.theblock.co/latest"
    try:
        html = _fetch(url)
        items = _parse_theblock(html, url)
        today = date.today()
        for item in items:
            item.published = today
        return items
    except RuntimeError:
        return []


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def run_monitor(
    days_back: int = 2,
    min_score: int = 1,
    top_n: int = 10,
) -> list[NewsItem]:
    """
    Full pipeline: fetch → parse → score → dedupe → rank.

    Returns up to `top_n` items sorted by relevance_score descending.
    """
    raw: list[NewsItem] = []
    raw.extend(fetch_cryptointegrat(days_back=days_back))
    raw.extend(fetch_theblock())

    # Score all items
    scored = [_score_item(item) for item in raw]

    # Keep only items with keyword matches
    filtered = [i for i in scored if i.relevance_score >= min_score]

    # Deduplicate by title similarity (simple: same first 60 chars)
    seen: set[str] = set()
    deduped: list[NewsItem] = []
    for item in filtered:
        key = item.title[:60].lower()
        if key not in seen:
            seen.add(key)
            deduped.append(item)

    # Sort by score
    deduped.sort(key=lambda i: i.relevance_score, reverse=True)

    return deduped[:top_n]


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_report(items: list[NewsItem], calendar: dict | None = None) -> str:
    """
    Format a human-readable Markdown report.
    `calendar` maps ISO date strings to {"project": ..., "format": ...}
    """
    if not items:
        return "No relevant news found in the last 2 days. Check back tomorrow."

    lines = ["# 📰 News Monitor — Content Recommendations\n"]
    lines.append(f"_Generated: {datetime.now().strftime('%d %b %Y, %H:%M')}_\n")

    # Group by project
    by_project: dict[str, list[NewsItem]] = {}
    for item in items:
        if item.matched_projects:
            proj = item.matched_projects[0]
            by_project.setdefault(proj, []).append(item)

    project_order = ["MAADS", "AADS", "Slise", "Welldone"]
    for proj in project_order:
        proj_items = by_project.get(proj, [])
        if not proj_items:
            continue

        lines.append(f"## {proj}\n")
        for idx, item in enumerate(proj_items[:3], 1):
            lines.append(f"### {idx}. {item.title}")
            lines.append(f"**Source:** {item.source}  ")
            if item.published:
                lines.append(f"**Date:** {item.published.strftime('%d %b %Y')}  ")
            lines.append(f"**Relevance score:** {item.relevance_score}  ")
            if item.post_angle:
                lines.append(f"**Suggested format:** {item.post_angle}  ")

            # Find next matching post date in calendar
            if calendar and item.matched_projects:
                next_date = _find_next_post_date(proj, calendar)
                if next_date:
                    lines.append(f"**Use for post:** {next_date}  ")

            lines.append(f"\n> {item.summary[:280]}\n")
            lines.append(f"[Read more]({item.url})\n")

        lines.append("")

    return "\n".join(lines)


def _find_next_post_date(project: str, calendar: dict) -> Optional[str]:
    """Return the next upcoming post date for this project from the calendar."""
    today = date.today()
    future_dates = sorted([
        d for d, v in calendar.items()
        if v.get("project") == project
        and date.fromisoformat(d) >= today
        and date.fromisoformat(d) <= today + timedelta(days=LOOKAHEAD_DAYS)
    ])
    if future_dates:
        return datetime.fromisoformat(future_dates[0]).strftime("%d %b (%A)")
    return None


# ---------------------------------------------------------------------------
# Demo / quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Fetching news…")
    results = run_monitor(days_back=2, top_n=10)

    # Minimal calendar for demo
    demo_calendar: dict = {}
    today = date.today()
    for i in range(14):
        d = today + timedelta(days=i)
        proj = "MAADS" if d.day % 2 == 1 else "AADS"
        demo_calendar[d.isoformat()] = {"project": proj, "format": "Market Insight"}

    print(format_report(results, calendar=demo_calendar))
    print(f"\nTotal items found: {len(results)}")
