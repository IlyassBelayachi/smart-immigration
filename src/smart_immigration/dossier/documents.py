"""Lecture et comparaison des pièces fictives de la démonstration."""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal
from io import BytesIO
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from ..schemas import ApplicantProfile, ExtractedField

DocumentType = Literal["acceptance", "transcript", "financial"]
MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 10

# Les libellés sont ceux des trois spécimens fournis avec la démo.
DOCUMENT_FIELDS = {
    "acceptance": {
        "candidate_name": "Nom", "institution": "Établissement", "program": "Programme",
        "start_date": "Date de début", "end_date": "Date de fin",
    },
    "transcript": {
        "candidate_name": "Nom", "institution": "Établissement", "study_period": "Période d’études",
    },
    "financial": {
        "account_holder": "Titulaire", "amount": "Montant", "currency": "Devise", "issue_date": "Date d’émission",
    },
}


class Specimen(BaseModel):
    document_id: str = Field(min_length=1, max_length=64)
    document_type: DocumentType
    fields: list[ExtractedField] = Field(max_length=5)

    @model_validator(mode="after")
    def validate_fields(self) -> Specimen:
        expected = DOCUMENT_FIELDS[self.document_type]
        if len(self.fields) != len(expected) or {field.field_name for field in self.fields} != expected.keys():
            raise ValueError("Les champs doivent correspondre au type de pièce.")
        if any(field.document_id != self.document_id for field in self.fields):
            raise ValueError("Les champs doivent appartenir à la même pièce.")
        if any(field.value and len(field.value) > 160 for field in self.fields):
            raise ValueError("Un champ ne peut pas dépasser 160 caractères.")
        return self


class Contradiction(BaseModel):
    field_name: str
    document_ids: list[str]
    message: str


def _normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold().replace("’", "'"))
    return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).split())


def _read_pages(content: bytes, media_type: str) -> list[list[tuple[str, float | None]]]:
    if media_type == "text/plain":
        try:
            return [[(line, None) for line in content.decode("utf-8-sig").splitlines()]]
        except UnicodeDecodeError as error:
            raise ValueError("Le fichier texte doit être encodé en UTF-8.") from error

    if not content.startswith(b"%PDF-"):
        raise ValueError("Le fichier ne contient pas un PDF valide.")
    try:
        pdf = PdfReader(BytesIO(content))
        if pdf.is_encrypted or len(pdf.pages) > MAX_PAGES:
            raise ValueError("Le PDF doit être lisible sans mot de passe et contenir au plus 10 pages.")
        pages = [page.extract_text() for page in pdf.pages]
        scanned_indexes = [
            index for index, text in enumerate(pages)
            if not text.strip() and pdf.pages[index].get_contents() is not None
        ]
    except (PyPdfError, OSError, RecursionError) as error:
        raise ValueError("Impossible de lire ce PDF.") from error
    scanned = {}
    if scanned_indexes:
        from .ocr import read_scanned_pages

        scanned = read_scanned_pages(content, scanned_indexes)
    return [scanned.get(index, [(line, None) for line in text.splitlines()]) for index, text in enumerate(pages)]


def extract_fields(content: bytes, document_type: DocumentType, media_type: str) -> Specimen:
    pages = _read_pages(content, media_type)
    if not any(_normalize(line) == "specimen" for page in pages for line, _ in page):
        raise ValueError("Le document doit comporter la mention SPÉCIMEN sur une ligne dédiée.")

    document_id = uuid4().hex
    candidates: dict[str, list[tuple[int, str, float | None]]] = {}
    for page_number, page in enumerate(pages, start=1):
        for line, confidence in page:
            label, separator, value = line.replace("：", ":").partition(":")
            value = value.strip()
            if separator and 0 < len(value) <= 160:
                candidates.setdefault(_normalize(label), []).append((page_number, value, confidence))

    fields = []
    for name, label in DOCUMENT_FIELDS[document_type].items():
        matches = candidates.get(_normalize(label), [])
        # Plusieurs valeurs différentes pour un même libellé exigent une saisie humaine.
        page, value, confidence = matches[0] if len({value for _, value, _ in matches}) == 1 else (None, None, None)
        fields.append(ExtractedField(
            document_id=document_id, field_name=name, value=value, page=page, confidence=confidence,
        ))
    return Specimen(document_id=document_id, document_type=document_type, fields=fields)


def _reviewed_values(document: Specimen) -> dict[str, str]:
    return {
        field.field_name: field.value.strip()
        for field in document.fields
        if field.reviewed_by_human and field.value and field.value.strip()
    }


def _financial_total(values: dict[str, str]) -> Decimal | None:
    amount = re.sub(r"\s+", "", values.get("amount", "")).replace(",", ".")
    if values.get("currency", "").upper() == "CAD" and re.fullmatch(r"[0-9]{1,12}(?:\.[0-9]{1,2})?", amount):
        return Decimal(amount)
    return None


def confirmed_funds(documents: list[Specimen]) -> Decimal | None:
    totals = {
        total for document in documents if document.document_type == "financial"
        if (total := _financial_total(_reviewed_values(document))) is not None
    }
    return totals.pop() if len(totals) == 1 else None


def find_contradictions(documents: list[Specimen], profile: ApplicantProfile) -> list[Contradiction]:
    names = {}
    totals = {}
    contradictions = []
    for document in documents:
        values = _reviewed_values(document)
        if "candidate_name" in values:
            names[document.document_id] = _normalize(values["candidate_name"])

        # Le spécimen financier représente le total déclaré. Le titulaire peut être un tiers.
        if document.document_type == "financial" and (total := _financial_total(values)) is not None:
            totals[document.document_id] = total
        else:
            continue
        if profile.funds_available_cad is not None and total != Decimal(str(profile.funds_available_cad)):
            contradictions.append(Contradiction(
                field_name="funds_available_cad", document_ids=[document.document_id],
                message="Le total du justificatif en CAD diffère des fonds déclarés dans le profil.",
            ))

    if len(set(names.values())) > 1:
        contradictions.append(Contradiction(
            field_name="candidate_name", document_ids=list(names),
            message="Le nom du candidat diffère entre les pièces confirmées.",
        ))
    if len(set(totals.values())) > 1:
        contradictions.append(Contradiction(
            field_name="amount", document_ids=list(totals),
            message="Les justificatifs confirmés indiquent des totaux différents en CAD.",
        ))
    return contradictions
