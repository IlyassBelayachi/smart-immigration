"""Contrats de donnees partages par tous les composants (agents, API, evaluation).

Regle du binome : on ne modifie ce fichier que par pull request relue par l'autre.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Verdict(str, Enum):
    """Etat d'un critere. UNKNOWN est un resultat legitime, pas une erreur."""

    MEETS = "MEETS"
    DOES_NOT_MEET = "DOES_NOT_MEET"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------- connaissances
class KnowledgeChunk(BaseModel):
    chunk_id: str
    source_id: str
    url: str
    title: str
    country: str = "CA"
    pathway: str = "study_permit"
    language: str = "en"
    retrieved_at: datetime
    published_at: datetime | None = None
    page_modified: str | None = None  # date "Page details" affichee par la source
    content_hash: str
    section: str | None = None
    text: str


class Evidence(BaseModel):
    """Preuve citable : permet a l'utilisateur de verifier la source."""

    source_id: str
    url: str
    title: str
    chunk_id: str
    section: str | None = None
    retrieved_at: datetime
    page_modified: str | None = None
    excerpt: str = Field(description="Extrait court (paraphrase ou passage), jamais la page entiere")


# ---------------------------------------------------------------- sortie d'agent
class AgentResult(BaseModel):
    """Contrat de sortie commun a tous les agents (cahier des charges, section 6)."""

    task_id: str
    agent: str
    status: Literal["ok", "abstained", "needs_human", "error"]
    data: dict[str, Any] = Field(default_factory=dict)
    evidence: list[Evidence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float | None = None  # exposee seulement si calibree
    model_version: str | None = None
    source_version: str | None = None
    timestamp: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------- profil candidat
class ApplicantProfile(BaseModel):
    """Profil minimal pour le permis d'etudes (Canada). Tous les champs sont optionnels :
    une valeur absente donne UNKNOWN, jamais une hypothese."""

    nationality: str | None = None
    residence_country: str | None = None
    application_date: date | None = None  # date de soumission prevue
    destination_province: str | None = None  # code ex. "QC", "ON"
    level_of_study: Literal["secondary", "college", "bachelor", "master", "phd", "other"] | None = None
    dli_is_public: bool | None = None
    has_letter_of_acceptance: bool | None = None
    pal_provided: bool | None = None
    pal_exemption_claimed: bool | None = None
    caq_provided: bool | None = None
    family_size: int | None = Field(default=None, ge=1, description="Candidat inclus")
    funds_available_cad: float | None = Field(default=None, ge=0)
    tuition_first_year_cad: float | None = Field(default=None, ge=0)
    transport_cost_cad: float | None = Field(default=None, ge=0)


# ---------------------------------------------------------------- regles
class RuleResult(BaseModel):
    rule_id: str
    title: str
    verdict: Verdict
    explanation: str
    rule_version: str
    source_urls: list[str]
    missing_inputs: list[str] = Field(default_factory=list)


class AssessmentReport(BaseModel):
    pathway: str
    rule_version: str
    generated_at: datetime = Field(default_factory=_now)
    results: list[RuleResult]
    disclaimer: str = (
        "Evaluation indicative et informative, non juridique. Elle ne remplace ni l'IRCC ni un conseil qualifie. "
        "Verifier chaque regle sur la page officielle citee."
    )


class ChecklistItem(BaseModel):
    rule_id: str
    title: str
    status: Literal["declared", "to_provide", "to_confirm", "not_assessed"]
    message: str
    missing_inputs: list[str] = Field(default_factory=list)
    source_urls: list[str]


class ChecklistResponse(BaseModel):
    pathway: str
    rule_version: str
    items: list[ChecklistItem]


# ---------------------------------------------------------------- champs extraits (S3)
class ExtractedField(BaseModel):
    document_id: str
    field_name: str
    value: str | None
    page: int | None = None
    bbox: tuple[float, float, float, float] | None = None
    confidence: float | None = None
    reviewed_by_human: bool = False


# ---------------------------------------------------------------- API
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    question: str
    answered: bool
    answer: str | None
    evidence: list[Evidence]
    abstention_reason: str | None = None
    retrieval: dict[str, Any] = Field(default_factory=dict)
