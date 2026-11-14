"""Routes de la chaîne DOSSIER (propriétaire : Personne 2)."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator
from starlette.concurrency import run_in_threadpool

from ..schemas import ApplicantProfile, AssessmentReport, ChecklistResponse
from .checklist import build_checklist
from .documents import MAX_BYTES, Contradiction, DocumentType, Specimen, confirmed_funds, extract_fields, find_contradictions
from .rules import DocumentCheck, DocumentCheckName, assess
from . import portal
from . import intake

router = APIRouter(tags=["dossier"])
router.include_router(portal.router)
router.include_router(intake.router)
SPECIMENS = Path(__file__).resolve().parents[3] / "data" / "synthetic"


class DossierRequest(BaseModel):
    profile: ApplicantProfile
    documents: list[Specimen] = Field(default_factory=list, max_length=6)
    document_checks: dict[DocumentCheckName, DocumentCheck] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_document_ids(self) -> DossierRequest:
        if len({piece.document_id for piece in self.documents}) != len(self.documents):
            raise ValueError("Chaque pièce doit avoir un identifiant distinct.")
        return self


class DossierReport(BaseModel):
    assessment: AssessmentReport
    checklist: ChecklistResponse
    contradictions: list[Contradiction]
    pending_fields: int
    can_validate: bool
    funds_from_documents_cad: float | None = None


@router.post("/assess", response_model=AssessmentReport)
def assess_profile(profile: ApplicantProfile) -> AssessmentReport:
    return assess(profile)


@router.post("/checklist", response_model=ChecklistResponse)
def get_checklist(profile: ApplicantProfile) -> ChecklistResponse:
    report = assess(profile)
    return build_checklist(profile, report)


@router.get("/dossier/specimens/{document_type}", include_in_schema=False)
def download_specimen(document_type: DocumentType, format: Literal["txt", "pdf"] = "txt") -> FileResponse:
    path = SPECIMENS / f"{document_type}.{format}"
    media_type = "application/pdf" if format == "pdf" else "text/plain"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.post("/dossier/documents/{document_type}", response_model=Specimen)
async def read_specimen(document_type: DocumentType, request: Request) -> Specimen:
    media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if media_type not in {"application/pdf", "text/plain"}:
        raise HTTPException(415, "Formats acceptés : PDF et texte UTF-8.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BYTES:
            raise HTTPException(413, "Le fichier dépasse la limite de 2 Mio.")
        content.extend(chunk)
    try:
        return await run_in_threadpool(extract_fields, bytes(content), document_type, media_type)
    except ValueError as error:
        raise HTTPException(422, str(error)) from error


@router.post("/dossier/report", response_model=DossierReport)
def get_dossier_report(dossier: DossierRequest) -> DossierReport:
    profile = dossier.profile
    contradictions = find_contradictions(dossier.documents, profile)
    funds = None
    if any(item.field_name in {"funds_available_cad", "amount"} for item in contradictions):
        profile = profile.model_copy(update={"funds_available_cad": None})
    elif profile.funds_available_cad is None:
        funds = confirmed_funds(dossier.documents)
        if funds is not None:
            profile = profile.model_copy(update={"funds_available_cad": float(funds)})
    assessment = assess(profile, document_checks=dossier.document_checks)
    pending_fields = sum(
        not (field.reviewed_by_human and field.value and field.value.strip())
        for piece in dossier.documents for field in piece.fields
    )
    return DossierReport(
        assessment=assessment,
        checklist=build_checklist(profile, assessment),
        contradictions=contradictions,
        pending_fields=pending_fields,
        can_validate=bool(dossier.documents) and pending_fields == 0 and not contradictions,
        funds_from_documents_cad=float(funds) if funds is not None else None,
    )


@router.post("/portal/cases", status_code=201)
def send_dossier(dossier: DossierRequest, account: dict = Depends(portal.current_account)):
    if account["role"] != "candidate":
        raise HTTPException(403, "Cette action est réservée aux candidats.")
    report = get_dossier_report(dossier)
    if not report.can_validate:
        raise HTTPException(422, "Confirmez les champs et résolvez les incohérences avant de transmettre le dossier.")
    return portal.submit_case(account, dossier.model_dump_json())
