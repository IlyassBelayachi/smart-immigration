"""Question -> reponse sourcee, ou abstention explicite.

Demo n°1 : reponse extractive (aucun LLM, donc aucune invention possible).
S4 : le Research Agent (LangGraph) reformule, itere et utilise ce module comme outil.
"""
from __future__ import annotations

import re

from .retrieval import Hit, LexicalIndex, content_tokens
from ..schemas import AskResponse, Evidence

# Seuils provisoires, a calibrer sur le jeu de questions annote (S3).
MIN_SCORE = 0.5
MIN_COVERAGE = 0.5


def _best_sentences(text: str, query: str, n: int = 2) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    q = set(content_tokens(query))
    ranked = sorted(sentences, key=lambda s: len(q & set(content_tokens(s))), reverse=True)
    keep = [s for s in ranked[:n] if q & set(content_tokens(s))]
    # on remet les phrases dans l'ordre d'origine
    return " ".join(s for s in sentences if s in keep)


def _evidence(hit: Hit, query: str) -> Evidence:
    c = hit.chunk
    return Evidence(
        source_id=c.source_id,
        url=c.url,
        title=c.title,
        chunk_id=c.chunk_id,
        section=c.section,
        retrieved_at=c.retrieved_at,
        page_modified=c.page_modified,
        excerpt=_best_sentences(c.text, query) or c.text[:300],
    )


def answer(index: LexicalIndex, question: str, top_k: int = 3) -> AskResponse:
    hits = index.search(question, k=top_k)
    meta = {
        "method": "bm25",
        "top_scores": [round(h.score, 3) for h in hits],
        "top_coverage": [round(h.coverage, 2) for h in hits],
    }
    if not hits or hits[0].score < MIN_SCORE or hits[0].coverage < MIN_COVERAGE:
        return AskResponse(
            question=question,
            answered=False,
            answer=None,
            evidence=[],
            abstention_reason="Aucun passage suffisamment pertinent dans le corpus officiel indexe.",
            retrieval=meta,
        )
    evidence = [_evidence(h, question) for h in hits if h.score >= MIN_SCORE and h.coverage >= MIN_COVERAGE]
    summary = evidence[0].excerpt
    return AskResponse(question=question, answered=True, answer=summary, evidence=evidence, retrieval=meta)
