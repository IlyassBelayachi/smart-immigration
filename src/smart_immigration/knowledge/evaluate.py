"""Evalue la recherche sur les questions annotees (data/eval/questions.jsonl).

    python -m smart_immigration.knowledge.evaluate          # depuis src/ ; ajouter RAG_EMBEDDINGS=1 pour comparer BM25 / hybride

Mesures : la bonne source est-elle dans les 3 premiers resultats (hit@3), et le systeme s'abstient-il
quand il n'y a rien dans le corpus (questions hors sujet).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from .qa import answer
from .retrieval import LexicalIndex, load_chunks

QUESTIONS = Path(__file__).resolve().parents[3] / "data" / "eval" / "questions.jsonl"


def load_questions(path: Path = QUESTIONS) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def evaluate(index, questions: list[dict], use_country: bool = False) -> dict:
    hit = abstain_ok = n_in = n_out = 0
    misses = []
    for q in questions:
        r = answer(index, q["q"], 3, q["country"] if use_country else None)
        if q["expect"] is None:
            n_out += 1
            abstain_ok += not r.answered
            if r.answered:
                misses.append((q["q"], "devait s'abstenir"))
        else:
            n_in += 1
            found = r.answered and q["expect"] in [e.source_id for e in r.evidence]
            hit += found
            if not found:
                got = [e.source_id for e in r.evidence] if r.answered else "abstention"
                misses.append((q["q"], f"attendu {q['expect']}, obtenu {got}"))
    return {"hit@3": f"{hit}/{n_in}", "abstentions correctes": f"{abstain_ok}/{n_out}", "ratees": misses}


def main() -> None:
    from .routes import get_index

    qs = load_questions()
    base = LexicalIndex(load_chunks())
    print("== BM25, tous pays ==", evaluate(base, qs))
    print("== BM25, filtre pays ==", evaluate(base, qs, use_country=True))
    if os.getenv("RAG_EMBEDDINGS") == "1":
        hybrid = get_index()
        print("== Hybride, tous pays ==", evaluate(hybrid, qs))
        print("== Hybride, filtre pays ==", evaluate(hybrid, qs, use_country=True))


if __name__ == "__main__":
    main()
