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

import numpy as np
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
    score: float  # score BM25 (mots-cles)
    coverage: float  # part des termes (hors mots vides) de la question presents dans le passage
    cosine: float | None = None  # ressemblance de sens (index vectoriel), si actif


def allowed_mask(chunks: list[KnowledgeChunk], country: str | None, pathway: str | None) -> list[bool]:
    """Vrai pour les passages du pays / parcours demandes (tous si aucun filtre)."""
    c = country.strip().upper() if country else None
    p = pathway.strip().lower() if pathway else None
    return [(c is None or ch.country.upper() == c) and (p is None or ch.pathway.lower() == p) for ch in chunks]


class LexicalIndex:
    method = "bm25"

    def __init__(self, chunks: list[KnowledgeChunk]):
        if not chunks:
            raise ValueError("corpus vide")
        self.chunks = chunks
        self._tokens = [content_tokens(f"{c.title} {c.section or ''} {c.text}") for c in chunks]
        self._sets = [set(t) for t in self._tokens]
        self._bm25 = BM25Okapi(self._tokens)

    def scores(self, query: str) -> tuple[np.ndarray, list[float]]:
        """Score BM25 et couverture de chaque passage pour la question."""
        q = content_tokens(query)
        if not q:
            return np.zeros(len(self.chunks)), [0.0] * len(self.chunks)
        qs = set(q)
        coverage = [sum(1 for t in qs if t in present) / len(qs) for present in self._sets]
        return np.asarray(self._bm25.get_scores(q), dtype=float), coverage

    def search(self, query: str, k: int = 3, country: str | None = None, pathway: str | None = None) -> list[Hit]:
        scores, coverage = self.scores(query)
        if not scores.any():
            return []
        ok = allowed_mask(self.chunks, country, pathway)
        order = [i for i in sorted(range(len(scores)), key=lambda i: scores[i], reverse=True) if ok[i]][:k]
        return [Hit(self.chunks[i], float(scores[i]), coverage[i]) for i in order]
