"""Saisie et pièces jointes pour les projets d’immigration."""
from __future__ import annotations

import base64
import binascii
import json
import re
from datetime import date
from io import BytesIO
from typing import Literal
from urllib.parse import quote
from zipfile import BadZipFile, ZipFile

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field, ValidationError
from starlette.concurrency import run_in_threadpool

from .portal import current_account, database, submit_case

router = APIRouter(prefix="/portal", tags=["dossier"])
COUNTRIES = (
    ("ES", "Espagne", 1088408, "https://home-affairs.ec.europa.eu/policies/migration-and-asylum/eu-immigration-portal_en"),
    ("FR", "France", 1066129, "https://france-visas.gouv.fr/"),
    ("IT", "Italie", 472734, "https://home-affairs.ec.europa.eu/policies/migration-and-asylum/eu-immigration-portal_en"),
    ("BE", "Belgique", 246575, "https://home-affairs.ec.europa.eu/policies/migration-and-asylum/eu-immigration-portal_en"),
    ("IL", "Israël", 190607, "https://israel-entry.piba.gov.il/visa-option"),
    ("NL", "Pays-Bas", 176423, "https://home-affairs.ec.europa.eu/policies/migration-and-asylum/eu-immigration-portal_en"),
    ("DE", "Allemagne", 156555, "https://home-affairs.ec.europa.eu/policies/migration-and-asylum/eu-immigration-portal_en"),
    ("CA", "Canada", 94694, "https://www.canada.ca/en/services/immigration-citizenship.html"),
    ("TR", "Turquie", 27080, "https://en.goc.gov.tr/residence-permit-types"),
    ("CH", "Suisse", 21949, "https://www.sem.admin.ch/sem/fr/home/themen.html"),
)
PURPOSES = {"work": "Travail", "study": "Études", "family": "Famille", "visit": "Visite",
            "permanent": "Résidence permanente", "other": "Autre projet"}
COMMON_FIELDS = {
    "residence": "Ville et pays de résidence",
    "situation": "Situation actuelle",
    "destination_city": "Ville de destination envisagée",
    "duration": "Durée du séjour envisagée",
    "accompanying": "Proches qui vous accompagnent",
    "funding": "Source de financement prévue",
}
PURPOSE_FIELDS = {
    "work": {"occupation": "Métier ou poste recherché", "employer": "Employeur ou secteur visé",
             "experience": "Expérience professionnelle", "offer": "Offre d’emploi ou contrat"},
    "study": {"institution": "Établissement", "programme": "Programme envisagé",
              "study_level": "Niveau d’études", "admission": "État de la candidature ou de l’admission"},
    "family": {"relationship": "Lien avec le proche", "sponsor_status": "Statut du proche dans le pays",
               "sponsor_city": "Ville de résidence du proche"},
    "visit": {"visit_reason": "Objet de la visite", "accommodation": "Hébergement prévu",
              "return_plan": "Retour envisagé"},
    "permanent": {"programme": "Programme d’immigration envisagé", "occupation": "Métier",
                  "education": "Diplôme le plus élevé", "languages": "Langues et tests passés"},
    "other": {"programme": "Démarche envisagée", "milestone": "Étapes déjà effectuées"},
}
FILE_KINDS = {"photo": "Photo du visage", "cv": "CV", "certificate": "Attestation",
              "police": "Casier judiciaire", "identity": "Pièce d’identité", "other": "Autre justificatif"}
MAX_FILE = 4 * 1024 * 1024
MAX_BODY = 18 * 1024 * 1024
FORMAT_TYPES = {
    "pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


class Attachment(BaseModel):
    kind: Literal["photo", "cv", "certificate", "police", "identity", "other"]
    filename: str = Field(min_length=1, max_length=120)
    data: str = Field(max_length=4 * ((MAX_FILE + 2) // 3))


class Intake(BaseModel):
    destination: Literal["ES", "FR", "IT", "BE", "IL", "NL", "DE", "CA", "TR", "CH"]
    purpose: Literal["work", "study", "family", "visit", "permanent", "other"]
    planned_date: date | None = None
    description: str = Field(min_length=1, max_length=2500)
    details: dict[str, str] = Field(default_factory=dict, max_length=10)
    files: list[Attachment] = Field(default_factory=list, max_length=3)


@router.get("/catalog")
def catalog():
    return {
        "countries": [{"code": code, "name": name, "stock_2024": stock, "url": url}
                      for code, name, stock, url in COUNTRIES],
        "purposes": PURPOSES, "file_kinds": FILE_KINDS,
        "common_fields": COMMON_FIELDS, "purpose_fields": PURPOSE_FIELDS,
    }


def _decode_file(file: Attachment) -> tuple[str, str, str, bytes]:
    if not re.fullmatch(r"[^/\\\x00-\x1f\x7f]+", file.filename):
        raise ValueError("Nom de fichier invalide.")
    extension = file.filename.rpartition(".")[2].lower()
    if extension not in FORMAT_TYPES:
        raise ValueError("Formats acceptés : PDF, JPG, PNG et DOCX.")
    if file.kind == "photo" and extension not in {"jpg", "jpeg", "png"}:
        raise ValueError("La photo doit être au format JPG ou PNG.")
    content = base64.b64decode(file.data, validate=True)
    if not content or len(content) > MAX_FILE:
        raise ValueError("Chaque fichier doit contenir au plus 4 Mio.")
    if extension == "pdf":
        if not content.startswith(b"%PDF-") or b"%%EOF" not in content[-2048:]:
            raise ValueError("PDF invalide.")
    elif extension == "docx":
        with ZipFile(BytesIO(content)) as archive:
            names = set(archive.namelist())
            if not {"[Content_Types].xml", "word/document.xml"} <= names or "word/vbaProject.bin" in names:
                raise ValueError("Document Word DOCX invalide.")
    else:
        with Image.open(BytesIO(content)) as image:
            expected = "PNG" if extension == "png" else "JPEG"
            if image.format != expected or image.width * image.height > 20_000_000:
                raise ValueError("Image invalide ou trop grande.")
            image.verify()
    return file.kind, file.filename, FORMAT_TYPES[extension], content


def _submit(content: bytes, account: dict):
    try:
        intake = Intake.model_validate_json(content)
        description = intake.description.strip()
        if not description:
            raise ValueError("Décrivez votre projet.")
        fields = COMMON_FIELDS.keys() | PURPOSE_FIELDS[intake.purpose].keys()
        if not intake.details.keys() <= fields or any(len(value) > 240 for value in intake.details.values()):
            raise ValueError("Vérifiez les informations du projet.")
        files = [_decode_file(file) for file in intake.files]
    except ValidationError as error:
        raise HTTPException(422, "Vérifiez les champs du projet et les pièces jointes.") from error
    except (ValueError, BadZipFile, UnidentifiedImageError, Image.DecompressionBombError, OSError, binascii.Error) as error:
        raise HTTPException(422, "Pièce ou description invalide. Vérifiez le format et la taille des fichiers.") from error
    payload = intake.model_dump(mode="json", exclude={"files"})
    payload.update(kind="general", description=description,
                   details={key: value.strip() for key, value in intake.details.items() if value.strip()})
    return submit_case(account, json.dumps(payload, ensure_ascii=False), files)


@router.post("/intake", status_code=201)
async def submit_intake(request: Request, account: dict = Depends(current_account)):
    if account["role"] != "candidate":
        raise HTTPException(403, "Cette action est réservée aux candidats.")
    content = bytearray()
    async for chunk in request.stream():
        if len(content) + len(chunk) > MAX_BODY:
            raise HTTPException(413, "Dossier trop volumineux.")
        content.extend(chunk)
    return await run_in_threadpool(_submit, bytes(content), account)


@router.get("/cases/{case_id}/files/{file_id}")
def download_file(case_id: int, file_id: int, account: dict = Depends(current_account)):
    scope = "c.candidate_id = ?" if account["role"] == "candidate" else "(c.consultant_id = ? OR c.consultant_id IS NULL)"
    with database() as db:
        file = db.execute(
            "SELECT f.* FROM case_files f JOIN cases c ON c.id = f.case_id "
            "WHERE c.id = ? AND f.id = ? AND " + scope, (case_id, file_id, account["id"]),
        ).fetchone()
    if file is None:
        raise HTTPException(404, "Pièce introuvable.")
    return Response(file["content"], media_type=file["media_type"], headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(file["filename"], safe=""),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff",
    })
