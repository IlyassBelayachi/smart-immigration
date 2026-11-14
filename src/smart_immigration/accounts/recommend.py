"""Recommandation automatique jointe à une demande (le consultant décide, jamais l'agent)."""
from __future__ import annotations

from ..dossier.rules import assess
from ..schemas import ApplicantProfile


def recommend(motive: str, destination: str, profile: dict) -> dict:
    if (destination, motive) != ("CA", "study"):
        return {"coverage": "not_covered", "summary": "Pas encore de règles automatiques pour ce pays et ce motif : examen humain complet nécessaire.", "results": []}
    report = assess(ApplicantProfile(**profile))
    counts: dict[str, int] = {}
    for r in report.results:
        counts[r.verdict.value] = counts.get(r.verdict.value, 0) + 1
    if counts.get("DOES_NOT_MEET"):
        summary = "Au moins un critère n'est pas rempli : à examiner avec attention."
    elif counts.get("UNKNOWN"):
        summary = "Des informations manquent pour conclure sur certains critères."
    else:
        summary = "Tous les critères vérifiés par les règles sont remplis (le consultant reste décideur)."
    return {
        "coverage": "full", "summary": summary, "rule_version": report.rule_version, "counts": counts,
        "results": [{"rule_id": r.rule_id, "title": r.title, "verdict": r.verdict.value, "explanation": r.explanation,
                     "source_urls": r.source_urls} for r in report.results],
    }
