"""Question -> reponse sourcee, ou abstention explicite.

Demo n°1 : reponse extractive (aucun LLM, donc aucune invention possible).
S4 : le Research Agent (LangGraph) reformule, itere et utilise ce module comme outil.
"""
from __future__ import annotations

import re

from .retrieval import Hit, content_tokens
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
        country=c.country,
    )


def _passes(h: Hit) -> bool:
    # La porte reste lexicale (mots de la question presents dans le passage) : les vecteurs aident a CLASSER,
    # mais ne suffisent pas a repondre. Seuils provisoires, non calibres sur des questions reelles.
    return h.score >= MIN_SCORE and h.coverage >= MIN_COVERAGE


def answer(index, question: str, top_k: int = 3, country: str | None = None, pathway: str | None = None) -> AskResponse:
    hits = index.search(question, k=top_k, country=country, pathway=pathway)
    meta = {
        "method": getattr(index, "method", "bm25"),
        "filters": {"country": country, "pathway": pathway},
        "top_scores": [round(h.score, 3) for h in hits],
        "top_coverage": [round(h.coverage, 2) for h in hits],
    }
    if any(h.cosine is not None for h in hits):
        meta["top_cosine"] = [round(h.cosine or 0.0, 3) for h in hits]
    good = [h for h in hits if _passes(h)]
    if not good:
        scope = f" pour {country.upper()}" if country else ""
        return AskResponse(
            question=question,
            answered=False,
            answer=None,
            evidence=[],
            abstention_reason=f"Aucun passage suffisamment pertinent dans le corpus officiel indexe{scope}.",
            retrieval=meta,
        )
    evidence = [_evidence(h, question) for h in good]
    return AskResponse(question=question, answered=True, answer=evidence[0].excerpt, evidence=evidence, retrieval=meta)
