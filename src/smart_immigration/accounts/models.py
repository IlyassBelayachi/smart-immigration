"""Tables de la base de données."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, LargeBinary, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # candidate | consultant
    # Candidats seulement : pending_identity -> verified | resubmit_requested
    identity_status: Mapped[str] = mapped_column(String(30), default="pending_identity")
    cin_hash: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)  # unicité
    cin_enc: Mapped[str | None] = mapped_column(Text, nullable=True)       # CIN chiffrée
    passport_enc: Mapped[str | None] = mapped_column(Text, nullable=True)  # facultatif, ajouté plus tard
    failed_attempts: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IdentityDocument(Base):
    __tablename__ = "identity_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # profile_photo | cin
    filename: Mapped[str] = mapped_column(String(255))
    media_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class IdentityCheck(Base):
    """Trace de chaque passage de l'agent de vérification d'identité."""
    __tablename__ = "identity_checks"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    agent: Mapped[str] = mapped_column(String(60))
    outcome: Mapped[str] = mapped_column(String(30))  # verified | resubmit
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class ImmigrationRequest(Base):
    __tablename__ = "immigration_requests"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    motive: Mapped[str] = mapped_column(String(40))
    destination: Mapped[str] = mapped_column(String(2))
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    # submitted -> awaiting_review -> approved | rejected | needs_info
    status: Mapped[str] = mapped_column(String(30), default="awaiting_review")
    recommendation: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    decisions: Mapped[list["Decision"]] = relationship(back_populates="request", order_by="Decision.id")


class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("immigration_requests.id"), index=True)
    consultant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    decision: Mapped[str] = mapped_column(String(20))  # approved | rejected | needs_info
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    request: Mapped[ImmigrationRequest] = relationship(back_populates="decisions")


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(nullable=True)
    action: Mapped[str] = mapped_column(String(60))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
