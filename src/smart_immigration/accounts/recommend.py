"""Recommandation automatique jointe à une demande (le consultant décide, jamais l'agent)."""
from __future__ import annotations

from ..dossier.rules import assess
from ..schemas import ApplicantProfile

COMMON = {"residence": "Lieu de résidence", "situation": "Situation actuelle", "duration": "Durée envisagée",
          "funding": "Sources de financement", "project_description": "Description du projet",
          "nationality": "Nationalité", "departure": "Date de départ souhaitée",
          "education": "Diplôme le plus élevé et domaine", "career": "Parcours professionnel et responsabilités",
          "languages": "Langues et niveaux", "certifications": "Certifications et tests de langue",
          "budget": "Fonds disponibles et devise", "accompanying": "Personnes qui vous accompagnent",
          "housing": "Hébergement à l’arrivée", "local_support": "Contacts et soutien à destination",
          "previous_applications": "Demandes antérieures et résultats",
          "obstacles": "Contraintes et solutions envisagées"}
BY_MOTIVE = {
    "study": {"institution": "Établissement", "program": "Programme", "admission": "État de l’admission", "study_dates": "Calendrier et durée du programme", "study_cost": "Frais et bourses", "study_goal": "Objectif après le diplôme"},
    "work": {"occupation": "Métier", "experience": "Expérience", "offer": "Offre ou employeur", "work_terms": "Contrat, rémunération et durée", "work_location": "Lieu de travail prévu", "recognition": "Reconnaissance du diplôme ou autorisation d’exercice"},
    "skilled_work": {"occupation": "Métier", "experience": "Expérience", "qualification": "Diplôme ou qualification", "recognition": "Reconnaissance des qualifications", "work_location": "Ville ou secteur visé"},
    "family": {"relationship": "Lien familial", "sponsor_status": "Situation du proche", "sponsor_support": "Soutien matériel et hébergement", "family_timeline": "Historique du lien et projet de vie"},
    "entrepreneur": {"business": "Projet d’entreprise", "investment": "Investissement prévu", "business_plan": "Marché, prévisions et financement", "business_progress": "Démarches déjà réalisées"},
    "protection": {"contact_support": "Accompagnement associatif ou juridique (facultatif)"},
    "other": {"pathway": "Démarche envisagée ou points à clarifier"},
    "visit": {"visit_reason": "Objet de la visite", "accommodation": "Hébergement prévu", "itinerary": "Dates et itinéraire", "return_plan": "Projet de retour"},
}
COUNTRIES = {
    "CA": ("america", ("fr", "en")), "FR": ("europe", ("fr",)), "BE": ("europe", ("fr", "nl", "de")),
    "CH": ("europe", ("fr", "de", "it")), "DE": ("europe", ("de",)), "ES": ("europe", ("es",)),
    "IT": ("europe", ("it",)), "NL": ("europe", ("nl",)), "TR": ("asia", ("tr",)), "IL": ("asia", ("he",)),
}


def suggest(preferences: dict) -> list[dict]:
    results = []
    languages_requested = preferences.get("languages")
    if not isinstance(languages_requested, list):
        languages_requested = [preferences.get("language")]
    languages_requested = [language for language in languages_requested if isinstance(language, str) and language not in ("", "any")]
    for code, (region, languages) in COUNTRIES.items():
        if code in (preferences.get("excluded") or []):
            continue
        language_match = any(language in languages for language in languages_requested)
        if preferences.get("adapt") == "no" and languages_requested and not language_match:
            continue
        factors = [(code == preferences.get("contact"), 5, "Contact sur place"),
                   (language_match, 3, "Une langue indiquée est utilisée"),
                   (preferences.get("near_morocco") is True and code in {"ES", "FR", "IT"}, 4, "Proximité géographique avec le Maroc"),
                   (region == preferences.get("region"), 2, "Région souhaitée")]
        reasons = [label for match, _, label in factors if match]
        if reasons:
            results.append({"code": code, "reasons": reasons, "score": sum(weight for match, weight, _ in factors if match)})
    return sorted(results, key=lambda result: (-result["score"], result["code"]))[:3]


def recommend(motive: str, destination: str, profile: dict) -> dict:
    fields = COMMON | BY_MOTIVE.get(motive, {})
    preferences = profile.get("orientation")
    values = {label: value.strip() for key, label in fields.items()
              if isinstance(value := profile.get(key), str) and value.strip()}
    context = {"provided_fields": values, "missing_fields": [label for label in fields.values() if label not in values],
               "suggestions": suggest(preferences) if destination == "ZZ" and isinstance(preferences, dict) else []}
    if (destination, motive) != ("CA", "study"):
        summary = ("Destination à définir. Les pistes reposent sur les préférences déclarées."
                   if destination == "ZZ" else "Compatibilité indéterminée. Vérifiez les exigences officielles de ce parcours.")
        return {**context, "coverage": "not_covered", "summary": summary, "results": []}
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
        **context, "coverage": "full", "summary": summary, "rule_version": report.rule_version, "counts": counts,
        "results": [{"rule_id": r.rule_id, "title": r.title, "verdict": r.verdict.value, "explanation": r.explanation,
                     "source_urls": r.source_urls} for r in report.results],
    }
