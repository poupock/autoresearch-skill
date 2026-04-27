#!/usr/bin/env python3
"""Translate an EPUB book from English to Russian via the Claude API.

Usage:
    export ANTHROPIC_API_KEY=...
    python translate_epub.py book.epub book.ru.epub --glossary glossary.json

Pipeline:
    1. Open input EPUB (a ZIP), find all XHTML/HTML content files via the OPF manifest.
    2. For each content file, walk the DOM, collect text-bearing leaves, group them
       into ~1.5K-token chunks.
    3. Send each chunk to Claude with a cached system prompt + glossary. The chunk
       payload is a list of fragments separated by a sentinel; Claude returns the
       same number of translated fragments in the same order.
    4. Splice translations back into the DOM (preserving every tag, attr, and entity).
    5. Write the modified XHTML into the output EPUB; copy everything else verbatim.
    6. Checkpoint after every chunk so re-runs on the same output file resume.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import unquote

import anthropic
from bs4 import BeautifulSoup, NavigableString, Tag

CONTAINER_PATH = "META-INF/container.xml"
SEPARATOR = "\n<<<§§§>>>\n"
SKIP_PARENTS = {"script", "style", "code", "pre", "kbd", "samp", "var", "tt"}
HTML_MEDIA_TYPES = {"application/xhtml+xml", "text/html"}

# Default per-chunk size for the variable user message. ~6000 chars is roughly
# 1500-2000 input tokens of English prose; well under per-request limits and small
# enough that a single retry on schema violation is cheap.
DEFAULT_CHUNK_CHARS = 6000


@dataclass
class Chunk:
    """One translation unit: a list of source strings plus their DOM addresses."""

    file_path: str
    indices: list[int]          # indices into the file's flat NavigableString list
    sources: list[str]


def load_glossary(path: Optional[Path]) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected an object {{english: russian, ...}}")
    return {str(k): str(v) for k, v in data.items()}


def build_system_prompt(glossary: dict[str, str]) -> str:
    if glossary:
        glossary_block = "\n".join(
            f"  - {en} → {ru}" for en, ru in sorted(glossary.items())
        )
    else:
        glossary_block = "  (пусто — следуй общим правилам)"
    return f"""Ты — профессиональный литературный переводчик с английского на русский.

ПРАВИЛА ПЕРЕВОДА:
1. Переводи художественно, сохраняя авторский стиль, ритм, регистр и длину абзацев.
2. Кавычки — ёлочки «...», для вложенных — „...".
3. Тире в диалогах и репликах — длинное (—), не дефис.
4. Имена собственные транскрибируй по системе Поливанова/Ермоловича; если в глоссарии задан вариант — используй его.
5. Никогда не добавляй пояснений, комментариев, примечаний переводчика, сносок.
6. Числовые ссылки [1], [2], URL, e-mail, имена тегов и CSS-селекторы оставляй как есть; переводи только окружающий человеческий текст.
7. Если фрагмент уже на русском, цифровой, или это пустая строка / только пунктуация — верни его без изменений.

ФОРМАТ ВВОДА:
Список фрагментов, разделённых строкой <<<§§§>>> (точно эти 7 символов на отдельной строке).
Каждый фрагмент — отдельный текстовый узел из HTML (заголовок, абзац, элемент списка, фрагмент инлайн-текста).

ФОРМАТ ВЫВОДА:
Верни РОВНО столько же фрагментов в том же порядке, разделённых ТОЙ ЖЕ строкой <<<§§§>>>.
Без нумерации, без обёртки, без преамбулы. Только переведённый текст.

КРИТИЧНО: количество фрагментов на входе и на выходе должно совпадать побайтово по разделителю — иначе перевод невозможно вклеить обратно в HTML.

ГЛОССАРИЙ:
{glossary_block}
"""


# ---------- EPUB structure ----------

def find_opf_path(zf: zipfile.ZipFile) -> str:
    """Read META-INF/container.xml to locate the OPF package document."""
    raw = zf.read(CONTAINER_PATH).decode("utf-8")
    soup = BeautifulSoup(raw, "xml")
    rootfile = soup.find("rootfile")
    if rootfile is None or not rootfile.get("full-path"):
        raise ValueError("EPUB has no rootfile in container.xml")
    return rootfile["full-path"]


def list_content_files(zf: zipfile.ZipFile, opf_path: str) -> list[str]:
    """Return XHTML/HTML content file paths in spine order."""
    raw = zf.read(opf_path).decode("utf-8")
    soup = BeautifulSoup(raw, "xml")
    manifest: dict[str, str] = {}
    for item in soup.find_all("item"):
        if item.get("media-type") in HTML_MEDIA_TYPES:
            manifest[item["id"]] = unquote(item["href"])
    spine_ids = [ref.get("idref") for ref in soup.find_all("itemref")]
    base = os.path.dirname(opf_path)
    out: list[str] = []
    for idref in spine_ids:
        if idref and idref in manifest:
            href = manifest[idref]
            full = os.path.normpath(os.path.join(base, href)) if base else href
            out.append(full.replace(os.sep, "/"))
    return out


# ---------- text extraction ----------

def collect_text_nodes(soup: BeautifulSoup) -> list[NavigableString]:
    """Collect leaf text nodes worth translating, in document order.

    Skips empty/whitespace-only nodes and any text whose ancestor is in SKIP_PARENTS.
    """
    nodes: list[NavigableString] = []
    for node in soup.find_all(string=True):
        if not isinstance(node, NavigableString):
            continue
        if not node.strip():
            continue
        parent_names = {p.name for p in node.parents if isinstance(p, Tag)}
        if parent_names & SKIP_PARENTS:
            continue
        nodes.append(node)
    return nodes


def chunk_nodes(
    file_path: str, nodes: list[NavigableString], target_chars: int
) -> list[Chunk]:
    chunks: list[Chunk] = []
    cur_idx: list[int] = []
    cur_src: list[str] = []
    cur_len = 0
    for i, node in enumerate(nodes):
        text = str(node)
        if cur_len + len(text) > target_chars and cur_src:
            chunks.append(Chunk(file_path, cur_idx, cur_src))
            cur_idx, cur_src, cur_len = [], [], 0
        cur_idx.append(i)
        cur_src.append(text)
        cur_len += len(text)
    if cur_src:
        chunks.append(Chunk(file_path, cur_idx, cur_src))
    return chunks


# ---------- translation ----------

def translate_chunk(
    client: anthropic.Anthropic,
    model: str,
    system_prompt: str,
    sources: list[str],
    max_retries: int = 3,
) -> list[str]:
    """Send one chunk to Claude. Retries with exponential backoff on count mismatch."""
    payload = SEPARATOR.join(sources)
    last_err: Optional[str] = None
    for attempt in range(max_retries):
        response = client.messages.create(
            model=model,
            max_tokens=16000,
            system=[
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": payload}],
        )
        text = "".join(b.text for b in response.content if b.type == "text")
        parts = text.split(SEPARATOR.strip("\n"))
        # Trim leading/trailing whitespace introduced by separator handling.
        parts = [p.strip("\n") for p in parts]
        if len(parts) == len(sources):
            return parts
        last_err = (
            f"got {len(parts)} fragments, expected {len(sources)} "
            f"(attempt {attempt + 1}/{max_retries})"
        )
        sys.stderr.write(f"  ! mismatch: {last_err}\n")
        time.sleep(2 ** attempt)
    # Fallback: return originals so the file remains valid; the user can re-run.
    sys.stderr.write(f"  ! giving up on chunk: {last_err}; keeping source text\n")
    return sources


# ---------- checkpoint ----------

def load_checkpoint(path: Path) -> dict:
    if not path.exists():
        return {"files": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def save_checkpoint(path: Path, data: dict) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


# ---------- main pipeline ----------

def translate_epub(
    src_path: Path,
    dst_path: Path,
    glossary_path: Optional[Path],
    model: str,
    chunk_chars: int,
) -> None:
    glossary = load_glossary(glossary_path)
    system_prompt = build_system_prompt(glossary)
    client = anthropic.Anthropic()

    checkpoint_path = dst_path.with_suffix(dst_path.suffix + ".checkpoint.json")
    checkpoint = load_checkpoint(checkpoint_path)

    with zipfile.ZipFile(src_path, "r") as zin:
        opf_path = find_opf_path(zin)
        content_files = list_content_files(zin, opf_path)
        all_names = zin.namelist()

        with zipfile.ZipFile(
            dst_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as zout:
            # mimetype must be the first entry, stored uncompressed.
            if "mimetype" in all_names:
                zout.writestr(
                    zipfile.ZipInfo("mimetype"),
                    zin.read("mimetype"),
                    compress_type=zipfile.ZIP_STORED,
                )

            for name in all_names:
                if name == "mimetype":
                    continue
                if name in content_files:
                    translated = translate_one_file(
                        client=client,
                        model=model,
                        system_prompt=system_prompt,
                        chunk_chars=chunk_chars,
                        name=name,
                        raw=zin.read(name),
                        checkpoint=checkpoint,
                        checkpoint_path=checkpoint_path,
                    )
                    zout.writestr(name, translated)
                else:
                    zout.writestr(name, zin.read(name))

    # Translation complete; the checkpoint file has served its purpose.
    if checkpoint_path.exists():
        checkpoint_path.unlink()
    sys.stderr.write(f"\nDone: {dst_path}\n")


def translate_one_file(
    *,
    client: anthropic.Anthropic,
    model: str,
    system_prompt: str,
    chunk_chars: int,
    name: str,
    raw: bytes,
    checkpoint: dict,
    checkpoint_path: Path,
) -> bytes:
    """Translate a single XHTML file. Returns the new file body."""
    sys.stderr.write(f"[{name}]\n")
    soup = BeautifulSoup(raw, "lxml-xml")  # preserves XHTML namespaces
    nodes = collect_text_nodes(soup)
    if not nodes:
        return raw

    file_state = checkpoint["files"].setdefault(name, {"chunks": {}})
    chunks = chunk_nodes(name, nodes, chunk_chars)

    for chunk_id, chunk in enumerate(chunks):
        cached = file_state["chunks"].get(str(chunk_id))
        if cached and len(cached) == len(chunk.sources):
            translations = cached
            sys.stderr.write(
                f"  chunk {chunk_id + 1}/{len(chunks)} (cached, "
                f"{len(chunk.sources)} fragments)\n"
            )
        else:
            sys.stderr.write(
                f"  chunk {chunk_id + 1}/{len(chunks)} "
                f"({len(chunk.sources)} fragments, "
                f"{sum(len(s) for s in chunk.sources)} chars)\n"
            )
            translations = translate_chunk(
                client, model, system_prompt, chunk.sources
            )
            file_state["chunks"][str(chunk_id)] = translations
            save_checkpoint(checkpoint_path, checkpoint)

        for node_idx, translated in zip(chunk.indices, translations):
            node = nodes[node_idx]
            node.replace_with(NavigableString(translated))

    return str(soup).encode("utf-8")


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Translate an EPUB book from English to Russian using Claude.",
    )
    parser.add_argument("input", type=Path, help="Source .epub")
    parser.add_argument("output", type=Path, help="Destination .epub")
    parser.add_argument(
        "--glossary",
        type=Path,
        default=Path("glossary.json"),
        help="Glossary JSON ({english: russian, ...}). Default: glossary.json",
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-6",
        help="Claude model. Default: claude-sonnet-4-6 "
        "(use claude-opus-4-7 for highest quality, claude-haiku-4-5 for cheapest).",
    )
    parser.add_argument(
        "--chunk-chars",
        type=int,
        default=DEFAULT_CHUNK_CHARS,
        help=f"Target chars per request. Default: {DEFAULT_CHUNK_CHARS}",
    )
    args = parser.parse_args(argv)

    if not args.input.exists():
        parser.error(f"input not found: {args.input}")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        parser.error("ANTHROPIC_API_KEY not set")

    translate_epub(
        src_path=args.input,
        dst_path=args.output,
        glossary_path=args.glossary if args.glossary.exists() else None,
        model=args.model,
        chunk_chars=args.chunk_chars,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
