"""Routes : /auth (connexion, profil), /requests, /consultant. L'inscription candidat est dans signup.py."""
from __future__ import annotations

import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import security
from .common import (DUMMY_HASH, audit, clean_cin, clean_passport, current_user, email_confirmation_required,  # noqa: F401
                     public, require, start_session)
from .db import get_session
from .models import Decision, ImmigrationRequest, User
from .recommend import recommend
from .recovery import router as recovery_router
from .signup import get_identity_agent, router as signup_router  # noqa: F401  (get_identity_agent réexporté pour les tests)

router = APIRouter(tags=["accounts"])
router.include_router(signup_router)
router.include_router(recovery_router)


# ---------- Authentification ----------
class ConsultantRegisterBody(BaseModel):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    role: Literal["candidate", "consultant"] = "consultant"
    invitation: str = Field(default="", max_length=128)


class LoginBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


@router.post("/auth/register", status_code=201)
def register_consultant(body: ConsultantRegisterBody, db: Session = Depends(get_session)):
    """Comptes consultants uniquement (code d'invitation). Les candidats passent par /auth/signup."""
    if body.role != "consultant":
        raise HTTPException(403, "Un compte candidat se crée avec la vérification d'identité (CIN + webcam).")
    invite = os.environ.get("CONSULTANT_INVITE", "")
    if not invite or not hmac.compare_digest(invite.encode(), body.invitation.encode()):
        raise HTTPException(403, "Un code d'invitation valide est requis pour un compte consultant.")
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Cette adresse est déjà utilisée.")
    user = User(email=email, full_name=body.full_name.strip(), role="consultant", identity_status="n/a",
                email_verified=True, password_hash=security.hash_password(body.password))
    db.add(user)
    db.flush()
    audit(db, user.id, "register", "consultant")
    return public(user)


@router.post("/auth/login")
def login(body: LoginBody, response: Response, db: Session = Depends(get_session)):
    user = db.scalar(select(User).where(User.email == body.email.strip().lower()))
    now = datetime.now(timezone.utc)
    if user and user.locked_until:
        until = user.locked_until if user.locked_until.tzinfo else user.locked_until.replace(tzinfo=timezone.utc)
        if until > now:
            raise HTTPException(429, "Trop d'essais. Réessayez dans quelques minutes.")
    ok = security.verify_password(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not ok:
        if user:
            user.failed_attempts += 1
            if user.failed_attempts >= security.MAX_FAILED:
                user.locked_until = now + timedelta(minutes=security.LOCK_MINUTES)
                user.failed_attempts = 0
                audit(db, user.id, "lockout")
            db.commit()
        raise HTTPException(401, "Adresse ou mot de passe incorrect.")
    if user.role == "candidate" and email_confirmation_required() and not user.email_verified:
        raise HTTPException(403, "Confirmez d'abord votre adresse email (lien envoyé à l'inscription).")
    user.failed_attempts, user.locked_until = 0, None
    audit(db, user.id, "login")
    start_session(response, user)
    return public(user)


@router.post("/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(security.COOKIE)


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return public(user)


class ProfileBody(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    passport: str | None = Field(default=None, max_length=20)

    @field_validator("passport")
    @classmethod
    def check_passport(cls, v):
        return clean_passport(v) if v else None


@router.patch("/auth/me")
def update_profile(body: ProfileBody, user: User = Depends(current_user), db: Session = Depends(get_session)):
    """Le candidat complète son profil. La CIN ne se change pas (liée à la vérification d'identité)."""
    if body.full_name:
        user.full_name = body.full_name.strip()
    if body.passport:
        if user.role != "candidate":
            raise HTTPException(403, "Le passeport concerne les comptes candidats.")
        user.passport_enc = security.encrypt(body.passport)
    audit(db, user.id, "profile_update")
    return public(user)


# ---------- Demandes d'immigration (candidat) ----------
class RequestBody(BaseModel):
    motive: Literal["study", "work", "family", "skilled_work", "entrepreneur", "visit", "protection", "other"]
    destination: str = Field(pattern=r"^[A-Z]{2}$")
    profile: dict = Field(default_factory=dict)
    passport: str | None = Field(default=None, max_length=20)  # facultatif, peut être ajouté ici

    @field_validator("passport")
    @classmethod
    def check_passport(cls, v):
        return clean_passport(v) if v else None


def serialize(r: ImmigrationRequest) -> dict:
    return {"id": r.id, "user_id": r.user_id, "motive": r.motive, "destination": r.destination, "status": r.status,
            "profile": r.profile, "recommendation": r.recommendation, "created_at": r.created_at.isoformat(),
            "decisions": [{"decision": d.decision, "reason": d.reason, "created_at": d.created_at.isoformat()}
                          for d in r.decisions]}


@router.post("/requests", status_code=201)
def create_request(body: RequestBody, user: User = Depends(require("candidate")), db: Session = Depends(get_session)):
    if user.identity_status != "verified":
        raise HTTPException(403, "Votre identité doit d'abord être vérifiée.")
    if body.passport:
        user.passport_enc = security.encrypt(body.passport)
    try:
        rec = recommend(body.motive, body.destination, body.profile)
    except ValueError as error:
        raise HTTPException(422, f"Profil invalide : {error}") from error
    req = ImmigrationRequest(user_id=user.id, motive=body.motive, destination=body.destination,
                             profile=body.profile, recommendation=rec)
    db.add(req)
    db.flush()
    audit(db, user.id, "request_created", f"{req.id}")
    return serialize(req)


@router.get("/requests")
def my_requests(user: User = Depends(require("candidate")), db: Session = Depends(get_session)):
    rows = db.scalars(select(ImmigrationRequest).where(ImmigrationRequest.user_id == user.id).order_by(ImmigrationRequest.id.desc()))
    return [serialize(r) for r in rows]


# ---------- Consultant : examine les demandes et décide ----------
class DecisionBody(BaseModel):
    decision: Literal["approved", "rejected", "needs_info"]
    reason: str = Field(min_length=3, max_length=2000)


@router.get("/consultant/requests")
def consultant_list(status: str | None = None, user: User = Depends(require("consultant")), db: Session = Depends(get_session)):
    q = select(ImmigrationRequest).order_by(ImmigrationRequest.id)
    if status:
        q = q.where(ImmigrationRequest.status == status)
    return [serialize(r) for r in db.scalars(q)]


@router.post("/consultant/requests/{request_id}/decision")
def consultant_decide(request_id: int, body: DecisionBody, user: User = Depends(require("consultant")),
                      db: Session = Depends(get_session)):
    req = db.get(ImmigrationRequest, request_id)
    if req is None:
        raise HTTPException(404, "Demande introuvable.")
    if req.status in {"approved", "rejected"}:
        raise HTTPException(409, "Cette demande est déjà clôturée.")
    db.add(Decision(request_id=req.id, consultant_id=user.id, decision=body.decision, reason=body.reason.strip()))
    req.status = body.decision
    audit(db, user.id, "decision", f"{req.id}:{body.decision}")
    db.flush()
    db.refresh(req)
    return serialize(req)
