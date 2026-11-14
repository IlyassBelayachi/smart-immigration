"""Ingestion des pages officielles -> data/corpus/chunks.jsonl (a lancer sur VOTRE machine, avec acces reseau).

    python -m smart_immigration.knowledge.ingest            # depuis le dossier src/

Chaque chunk conserve : URL, titre, section, date de collecte, date "Page details" et empreinte du contenu
(pour detecter les changements). Verifier les conditions de reutilisation du site avant tout usage au-dela du PFA.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
SOURCES = ROOT / "data" / "sources.yaml"
OUT = ROOT / "data" / "corpus" / "chunks.jsonl"
MAX_CHARS = 900


def parse_page(html: str) -> tuple[str | None, list[tuple[str, str]]]:
    """Retourne (date 'Page details', [(section, texte), ...]) a partir du HTML canada.ca."""
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    for tag in main.find_all(["nav", "script", "style", "form", "select", "footer"]):
        tag.decompose()

    modified = None
    meta = soup.find("meta", attrs={"name": "dcterms.modified"})
    if meta and meta.get("content"):
        modified = meta["content"]

    sections: list[tuple[str, list[str]]] = [("Intro", [])]
    for el in main.find_all(["h1", "h2", "h3", "p", "li"]):
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))
        if not text:
            continue
        if el.name in ("h1", "h2", "h3"):
            sections.append((text, []))
        else:
            sections[-1][1].append(text)
    return modified, [(title, " ".join(parts)) for title, parts in sections if parts]


def split_text(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, cur = [], ""
    for s in sentences:
        if cur and len(cur) + len(s) + 1 > max_chars:
            chunks.append(cur)
            cur = s
        else:
            cur = f"{cur} {s}".strip()
    if cur:
        chunks.append(cur)
    return chunks


def build_chunks(src: dict, html: str, country: str, pathway: str, language: str) -> list[dict]:
    modified, sections = parse_page(html)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for section, text in sections:
        for i, piece in enumerate(split_text(text), start=1):
            out.append(
                {
                    "chunk_id": f"{src['source_id']}#{len(out) + 1}",
                    "source_id": src["source_id"],
                    "url": src["url"],
                    "title": src["title"],
                    "country": country,
                    "pathway": pathway,
                    "language": language,
                    "retrieved_at": now,
                    "published_at": None,
                    "page_modified": modified or src.get("page_modified"),
                    "content_hash": hashlib.sha256(piece.encode("utf-8")).hexdigest()[:16],
                    "section": section,
                    "text": piece,
                }
            )
    return out


def main() -> None:
    cfg = yaml.safe_load(SOURCES.read_text(encoding="utf-8"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    with OUT.open("w", encoding="utf-8") as f, httpx.Client(timeout=30, follow_redirects=True,
                                                            headers={"User-Agent": "EMSI-PFA-research/0.1"}) as client:
        for src in cfg["sources"]:
            try:
                r = client.get(src["url"])
                r.raise_for_status()
            except httpx.HTTPError as e:
                print(f"[SKIP] {src['source_id']}: {e}", file=sys.stderr)
                continue
            chunks = build_chunks(src, r.text, cfg["country"], cfg["pathway"], cfg["language"])
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
            total += len(chunks)
            print(f"[OK] {src['source_id']}: {len(chunks)} chunks")
    print(f"Ecrit {total} chunks dans {OUT}")


if __name__ == "__main__":
    main()
