"""Routes de la chaîne CONNAISSANCE (propriétaire : Personne 1)."""
from __future__ import annotations

from functools import lru_cache

from fastapi import APIRouter

from ..schemas import AskRequest, AskResponse
from .qa import answer
from .retrieval import LexicalIndex, load_chunks

router = APIRouter(tags=["connaissance"])


@lru_cache(maxsize=1)
def get_index() -> LexicalIndex:
    return LexicalIndex(load_chunks())


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "chunks": len(get_index().chunks)}


@router.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    return answer(get_index(), req.question, req.top_k)
