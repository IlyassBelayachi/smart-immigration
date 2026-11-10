"""Checklist indicative construite a partir des verdicts du moteur de regles."""
from __future__ import annotations

from ..schemas import (
    ApplicantProfile,
    AssessmentReport,
    ChecklistItem,
    ChecklistResponse,
    Verdict,
)


def build_checklist(profile: ApplicantProfile, report: AssessmentReport) -> ChecklistResponse:
    items: list[ChecklistItem] = []

    for result in report.results:
        if result.rule_id == "CA-SP-003" and profile.destination_province:
            if profile.destination_province.upper() == "QC":
                items.append(
                    ChecklistItem(
                        rule_id=result.rule_id,
                        title=result.title,
                        status="not_assessed",
                        message="Le bareme federal encode ne couvre pas le Quebec. Verifier les exigences du MIFI.",
                        source_urls=result.source_urls,
                    )
                )
                continue

        if result.verdict == Verdict.MEETS:
            status = "declared"
            message = "Declare comme disponible dans le profil ; le document n'a pas ete verifie."
        elif result.verdict == Verdict.DOES_NOT_MEET:
            status = "to_provide"
            message = result.explanation
        else:
            status = "to_confirm"
            message = result.explanation

        items.append(
            ChecklistItem(
                rule_id=result.rule_id,
                title=result.title,
                status=status,
                message=message,
                missing_inputs=result.missing_inputs,
                source_urls=result.source_urls,
            )
        )

    return ChecklistResponse(
        pathway=report.pathway,
        rule_version=report.rule_version,
        items=items,
    )
