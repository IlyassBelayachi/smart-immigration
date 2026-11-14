"""Recherche dans le corpus reglementaire.

Demo n°1 : BM25 lexical + regle d'abstention.
S3 : ajouter l'index vectoriel (embeddings) et la fusion RRF -> RAG hybride (hypothese H1).
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from rank_bm25 import BM25Okapi

from ..schemas import KnowledgeChunk

ROOT = Path(__file__).resolve().parents[3]
CORPUS_PATH = ROOT / "data" / "corpus" / "chunks.jsonl"
SEED_PATH = ROOT / "data" / "seed" / "seed_chunks.jsonl"

_STOP = set(
    "a an and are as at be by can do does for from how i if in is it of on or the to what when which who will with "
    "you your my me we they there this that need needs have has must should".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [t for t in _TOKEN.findall(text)]


def content_tokens(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in _STOP and len(t) > 1]


def load_chunks(path: Path | None = None) -> list[KnowledgeChunk]:
    """Charge le corpus ingere ; a defaut, le corpus d'amorcage (paraphrases) pour la demo."""
    path = path or (CORPUS_PATH if CORPUS_PATH.exists() else SEED_PATH)
    with path.open(encoding="utf-8") as f:
        return [KnowledgeChunk.model_validate(json.loads(line)) for line in f if line.strip()]


@dataclass
class Hit:
    chunk: KnowledgeChunk
    score: float
    coverage: float  # part des termes (hors mots vides) de la question presents dans le passage


class LexicalIndex:
    def __init__(self, chunks: list[KnowledgeChunk]):
        if not chunks:
            raise ValueError("corpus vide")
        self.chunks = chunks
        self._tokens = [content_tokens(f"{c.title} {c.section or ''} {c.text}") for c in chunks]
        self._bm25 = BM25Okapi(self._tokens)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        q = content_tokens(query)
        if not q:
            return []
        scores = self._bm25.get_scores(q)
        order = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        hits = []
        for i in order:
            present = set(self._tokens[i])
            coverage = sum(1 for t in set(q) if t in present) / len(set(q))
            hits.append(Hit(self.chunks[i], float(scores[i]), coverage))
        return hits
