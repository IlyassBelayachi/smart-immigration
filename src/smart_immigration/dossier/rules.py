"""Moteur de regles declaratif et deterministe (aucun LLM ici).

Principe : une information manquante donne UNKNOWN avec la liste des champs manquants ; on ne devine jamais.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import yaml

from ..schemas import ApplicantProfile, AssessmentReport, RuleResult, Verdict

RULES_PATH = Path(__file__).resolve().parents[3] / "rules" / "study_permit_ca.yaml"


def load_ruleset(path: Path | None = None) -> dict[str, Any]:
    with (path or RULES_PATH).open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _result(rule: dict, version: str, verdict: Verdict, explanation: str, missing: list[str] | None = None) -> RuleResult:
    return RuleResult(
        rule_id=rule["id"],
        title=rule["title"],
        verdict=verdict,
        explanation=explanation,
        rule_version=version,
        source_urls=rule["source_urls"],
        missing_inputs=missing or [],
    )


# ------------------------------------------------------------------ evaluateurs
def _required_flag(rule: dict, p: ApplicantProfile, version: str) -> RuleResult:
    value = getattr(p, rule["field"])
    if value is None:
        return _result(rule, version, Verdict.UNKNOWN, "Information non renseignee.", [rule["field"]])
    if value:
        return _result(rule, version, Verdict.MEETS, rule["meets"])
    return _result(rule, version, Verdict.DOES_NOT_MEET, rule["fails"])


def _attestation_letter(rule: dict, p: ApplicantProfile, version: str) -> RuleResult:
    if p.destination_province is None:
        return _result(rule, version, Verdict.UNKNOWN, "Province de destination inconnue.", ["destination_province"])

    if p.destination_province.upper() == rule["quebec_code"]:
        # Au Quebec, le CAQ est requis meme pour la plupart des etudiants exemptes de PAL.
        if p.caq_provided is None:
            return _result(rule, version, Verdict.UNKNOWN, "Etudes au Quebec : CAQ requis, statut non renseigne.", ["caq_provided"])
        if p.caq_provided:
            return _result(rule, version, Verdict.MEETS, "Etudes au Quebec : attestation de delivrance du CAQ declaree.")
        return _result(rule, version, Verdict.DOES_NOT_MEET, "Etudes au Quebec : le CAQ est requis et n'est pas declare.")

    if p.level_of_study is None:
        return _result(rule, version, Verdict.UNKNOWN, "Niveau d'etudes inconnu : impossible de verifier l'exemption.", ["level_of_study"])

    if p.level_of_study in rule["exempt_levels"]:
        if p.dli_is_public is None:
            return _result(rule, version, Verdict.UNKNOWN, "Exemption possible (maitrise/doctorat) si le DLI est public ; statut du DLI inconnu.", ["dli_is_public"])
        if p.dli_is_public:
            return _result(
                rule, version, Verdict.MEETS,
                "Maitrise/doctorat dans un DLI public commencant a partir du 1er janvier 2026 : PAL/TAL non requis. "
                "Une preuve de l'exemption doit etre fournie avec la demande.",
            )

    if p.pal_provided is None and not p.pal_exemption_claimed:
        return _result(rule, version, Verdict.UNKNOWN, "PAL/TAL : statut non renseigne.", ["pal_provided"])
    if p.pal_provided:
        return _result(rule, version, Verdict.MEETS, "PAL/TAL declare. Il doit etre valide (annee de plafond en cours) et soumis avec la demande.")
    if p.pal_exemption_claimed:
        return _result(rule, version, Verdict.UNKNOWN, "Exemption revendiquee : a prouver avec des justificatifs, l'agent IRCC la confirmera.", [])
    return _result(rule, version, Verdict.DOES_NOT_MEET, "Aucun PAL/TAL declare et aucune exemption revendiquee. Verifier la liste officielle des exemptions.")


def _living_expenses(table: dict, family_size: int) -> float:
    sizes = table["per_family_size"]
    max_listed = max(sizes)
    if family_size <= max_listed:
        return float(sizes[family_size])
    return float(sizes[max_listed] + (family_size - max_listed) * table["extra_member"])


def _funds_threshold(rule: dict, p: ApplicantProfile, version: str) -> RuleResult:
    missing = [
        name
        for name in ("application_date", "family_size", "funds_available_cad", "tuition_first_year_cad", "transport_cost_cad")
        if getattr(p, name) is None
    ]
    if p.destination_province and p.destination_province.upper() == "QC":
        return _result(rule, version, Verdict.UNKNOWN, "Quebec : les couts sont fixes par le ministere quebecois (MIFI), hors du bareme federal encode ici.", [])
    if missing:
        return _result(rule, version, Verdict.UNKNOWN, "Donnees insuffisantes pour calculer le montant requis.", missing)

    table = _pick_table(rule["tables"], p.application_date)
    if table is None:
        return _result(rule, version, Verdict.UNKNOWN, f"Aucun bareme encode pour une demande au {p.application_date}.", ["application_date"])

    living = _living_expenses(table, p.family_size)
    required = living + p.tuition_first_year_cad + p.transport_cost_cad
    detail = (
        f"Requis = frais de vie {living:,.0f} + scolarite {p.tuition_first_year_cad:,.0f} + transport {p.transport_cost_cad:,.0f} "
        f"= {required:,.0f} CAD ; disponible : {p.funds_available_cad:,.0f} CAD."
    )
    if p.funds_available_cad >= required:
        return _result(rule, version, Verdict.MEETS, "Montant suffisant sur le papier. " + detail + " La source et la disponibilite reelle des fonds restent a prouver.")
    return _result(rule, version, Verdict.DOES_NOT_MEET, "Montant insuffisant. " + detail)


def _pick_table(tables: list[dict], on: date) -> dict | None:
    for t in tables:
        start = date.fromisoformat(str(t["from"]))
        end = date.fromisoformat(str(t["to"])) if t.get("to") else None
        if on >= start and (end is None or on <= end):
            return t
    return None


EVALUATORS = {
    "required_flag": _required_flag,
    "attestation_letter": _attestation_letter,
    "funds_threshold": _funds_threshold,
}


def assess(profile: ApplicantProfile, ruleset: dict[str, Any] | None = None) -> AssessmentReport:
    ruleset = ruleset or load_ruleset()
    version = ruleset["version"]
    results = [EVALUATORS[r["type"]](r, profile, version) for r in ruleset["rules"]]
    return AssessmentReport(pathway=ruleset["pathway"], rule_version=version, results=results)
