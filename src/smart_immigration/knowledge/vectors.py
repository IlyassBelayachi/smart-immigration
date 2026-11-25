"""Recherche par le SENS (embeddings) et fusion avec les mots-cles (RRF) = RAG hybride.

Un embedding transforme une phrase en une liste de nombres ; deux phrases de sens proche donnent des listes proches.
Ainsi "Do I need money proof?" retrouve un passage qui parle de "financial support", sans mot commun.
Le modele est charge a la demande (premiere utilisation = telechargement une seule fois). Sans le paquet `fastembed`,
l'application reste en BM25 seul.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Callable, Sequence

import numpy as np

from ..schemas import KnowledgeChunk
from .retrieval import Hit, LexicalIndex, allowed_mask

MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # FR/EN/AR..., leger
RRF_K = 60  # constante classique de la fusion par rangs

Embedder = Callable[[Sequence[str]], np.ndarray]


def fastembed_embedder(model_name: str = MODEL_NAME) -> Embedder:
    from fastembed import TextEmbedding  # import tardif : paquet facultatif

    model = TextEmbedding(model_name)

    def embed(texts: Sequence[str]) -> np.ndarray:
        return np.asarray(list(model.embed(list(texts))), dtype=np.float32)

    return embed


def _normalize(m: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(m, axis=1, keepdims=True)
    return m / np.where(n == 0, 1, n)


def chunk_text(c: KnowledgeChunk) -> str:
    return f"{c.title}. {c.section or ''}. {c.text}"


class VectorIndex:
    def __init__(self, chunks: list[KnowledgeChunk], embed: Embedder, cache: Path | None = None, tag: str = ""):
        self.chunks, self._embed = chunks, embed
        texts = [chunk_text(c) for c in chunks]
        key = hashlib.sha256((tag + "\n".join(texts)).encode("utf-8")).hexdigest()[:16]
        meta = cache.with_suffix(".json") if cache else None
        if cache and meta and cache.exists() and meta.exists() and json.loads(meta.read_text())["key"] == key:
            self.matrix = np.load(cache)
        else:
            self.matrix = _normalize(embed(texts))
            if cache and meta:
                cache.parent.mkdir(parents=True, exist_ok=True)
                np.save(cache, self.matrix)
                meta.write_text(json.dumps({"key": key, "n": len(chunks)}))

    def similarities(self, query: str) -> np.ndarray:
        return self.matrix @ _normalize(self._embed([query]))[0]


class HybridIndex:
    """BM25 (mots-cles) + vecteurs (sens), fusionnes par rangs (RRF)."""

    method = "hybrid-rrf"

    def __init__(self, lexical: LexicalIndex, vectors: VectorIndex):
        self.lexical, self.vectors, self.chunks = lexical, vectors, lexical.chunks

    def search(self, query: str, k: int = 3, country: str | None = None, pathway: str | None = None) -> list[Hit]:
        bm25, coverage = self.lexical.scores(query)
        cos = self.vectors.similarities(query)
        ok = allowed_mask(self.chunks, country, pathway)
        pool = [i for i in range(len(self.chunks)) if ok[i]]
        if not pool:
            return []
        rrf = dict.fromkeys(pool, 0.0)
        for ranking in (sorted(pool, key=lambda i: bm25[i], reverse=True), sorted(pool, key=lambda i: cos[i], reverse=True)):
            for rank, i in enumerate(ranking, start=1):
                rrf[i] += 1.0 / (RRF_K + rank)
        top = sorted(pool, key=lambda i: rrf[i], reverse=True)[:k]
        return [Hit(self.chunks[i], float(bm25[i]), coverage[i], float(cos[i])) for i in top]
