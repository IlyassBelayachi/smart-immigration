"""Routes de la chaîne DOSSIER (propriétaire : Personne 2)."""
from __future__ import annotations

from fastapi import APIRouter

from ..schemas import ApplicantProfile, AssessmentReport, ChecklistResponse
from .checklist import build_checklist
from .rules import assess

router = APIRouter(tags=["dossier"])


@router.post("/assess", response_model=AssessmentReport)
def assess_profile(profile: ApplicantProfile) -> AssessmentReport:
    return assess(profile)


@router.post("/checklist", response_model=ChecklistResponse)
def get_checklist(profile: ApplicantProfile) -> ChecklistResponse:
    report = assess(profile)
    return build_checklist(profile, report)
