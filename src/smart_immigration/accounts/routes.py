"""Routes : /auth, /identity, /requests, /consultant."""
from __future__ import annotations

import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import security
from .db import get_session
from .identity import DetectorUnavailable, IdentityAgent
from .models import AuditLog, Decision, IdentityCheck, IdentityDocument, ImmigrationRequest, User
from .recommend import recommend

router = APIRouter(tags=["accounts"])
MAX_UPLOAD = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png"}
DUMMY_HASH = security.hash_password("dummy-password-for-timing")


def get_identity_agent() -> IdentityAgent:
    return IdentityAgent()


def audit(db: Session, user_id: int | None, action: str, detail: str = "") -> None:
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))


def public(u: User) -> dict:
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role,
            "identity_status": u.identity_status if u.role == "candidate" else None}


def current_user(request: Request, db: Session = Depends(get_session)) -> User:
    payload = security.read_token(request.cookies.get(security.COOKIE, ""))
    user = db.get(User, int(payload["sub"])) if payload else None
    if user is None:
        raise HTTPException(401, "Connectez-vous pour continuer.")
    return user


def require(role: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, "Action réservée à un autre type de compte.")
        return user
    return dep


# ---------- Authentification ----------
class RegisterBody(BaseModel):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    role: Literal["candidate", "consultant"] = "candidate"
    invitation: str = Field(default="", max_length=128)


class LoginBody(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


@router.post("/auth/register", status_code=201)
def register(body: RegisterBody, db: Session = Depends(get_session)):
    if body.role == "consultant":
        invite = os.environ.get("CONSULTANT_INVITE", "")
        if not invite or not hmac.compare_digest(invite.encode(), body.invitation.encode()):
            raise HTTPException(403, "Un code d'invitation valide est requis pour un compte consultant.")
    email = body.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Cette adresse est déjà utilisée.")
    user = User(email=email, full_name=body.full_name.strip(), role=body.role,
                password_hash=security.hash_password(body.password),
                identity_status="pending_identity" if body.role == "candidate" else "n/a")
    db.add(user)
    db.flush()
    audit(db, user.id, "register", body.role)
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
    user.failed_attempts, user.locked_until = 0, None
    audit(db, user.id, "login")
    response.set_cookie(security.COOKIE, security.make_token(user.id, user.role), httponly=True,
                        samesite="strict", max_age=security.SESSION_HOURS * 3600)
    return public(user)


@router.post("/auth/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(security.COOKIE)


@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return public(user)


# ---------- Vérification d'identité (agent) ----------
async def _read_image(file: UploadFile) -> bytes:
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(422, "Formats acceptés : JPG ou PNG.")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Fichier trop gros (5 Mo maximum).")
    return data


@router.post("/identity/submit")
async def submit_identity(profile_photo: UploadFile = File(...), cin: UploadFile = File(...),
                          user: User = Depends(require("candidate")), db: Session = Depends(get_session),
                          agent: IdentityAgent = Depends(get_identity_agent)):
    if user.identity_status == "verified":
        raise HTTPException(409, "Votre identité est déjà vérifiée.")
    photo, cin_bytes = await _read_image(profile_photo), await _read_image(cin)
    for kind, f, data in (("profile_photo", profile_photo, photo), ("cin", cin, cin_bytes)):
        db.add(IdentityDocument(user_id=user.id, kind=kind, filename=(f.filename or kind)[:255],
                                media_type=f.content_type or "", content=data))
    try:
        verdict = agent.verify(photo, cin_bytes)
    except DetectorUnavailable as error:
        db.rollback()
        raise HTTPException(503, str(error)) from error
    db.add(IdentityCheck(user_id=user.id, agent=verdict.agent, outcome=verdict.outcome,
                         reasons=verdict.reasons, details=verdict.details))
    user.identity_status = "verified" if verdict.outcome == "verified" else "resubmit_requested"
    audit(db, user.id, "identity_check", verdict.outcome)
    return {"identity_status": user.identity_status, "reasons": verdict.reasons}


# ---------- Demandes d'immigration (candidat) ----------
class RequestBody(BaseModel):
    motive: Literal["study", "work", "family", "skilled_work", "entrepreneur", "visit", "protection", "other"]
    destination: str = Field(pattern=r"^[A-Z]{2}$")
    profile: dict = Field(default_factory=dict)


def serialize(r: ImmigrationRequest) -> dict:
    return {"id": r.id, "user_id": r.user_id, "motive": r.motive, "destination": r.destination, "status": r.status,
            "profile": r.profile, "recommendation": r.recommendation, "created_at": r.created_at.isoformat(),
            "decisions": [{"decision": d.decision, "reason": d.reason, "created_at": d.created_at.isoformat()}
                          for d in r.decisions]}


@router.post("/requests", status_code=201)
def create_request(body: RequestBody, user: User = Depends(require("candidate")), db: Session = Depends(get_session)):
    if user.identity_status != "verified":
        raise HTTPException(403, "Votre identité doit d'abord être vérifiée.")
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
