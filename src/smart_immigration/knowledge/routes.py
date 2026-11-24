"""Routes de la chaîne CONNAISSANCE (propriétaire : Personne 1)."""
from __future__ import annotations

import os
from functools import lru_cache

from fastapi import APIRouter

from ..schemas import AskRequest, AskResponse
from .qa import answer
from .retrieval import CORPUS_PATH, LexicalIndex, load_chunks

router = APIRouter(tags=["connaissance"])


@lru_cache(maxsize=1)
def get_index():
    """BM25 par defaut. Avec RAG_EMBEDDINGS=1 (et `pip install fastembed`) : recherche hybride mots-cles + sens."""
    lexical = LexicalIndex(load_chunks())
    if os.getenv("RAG_EMBEDDINGS") == "1":
        try:
            from .vectors import HybridIndex, VectorIndex, fastembed_embedder

            cache = CORPUS_PATH.parent / "vectors.npy"
            return HybridIndex(lexical, VectorIndex(lexical.chunks, fastembed_embedder(), cache))
        except ImportError:
            print("[RAG] fastembed absent : recherche par mots-cles seulement (pip install fastembed)")
    return lexical


@router.get("/health")
def health() -> dict:
    index = get_index()
    return {"status": "ok", "chunks": len(index.chunks), "method": index.method,
            "countries": sorted({c.country for c in index.chunks})}


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    return answer(get_index(), req.question, req.top_k, req.country, req.pathway)
