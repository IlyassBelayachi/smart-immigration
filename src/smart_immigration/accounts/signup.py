"""Inscription candidat : le compte n'est créé QU'APRÈS la vérification d'identité (CIN + webcam en direct)."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from . import liveness, mailer, security
from .common import audit, clean_cin, email_confirmation_required
from .db import get_session
from .face import DetectorUnavailable, OpenCVFaceService
from .identity import IdentityAgent
from .models import IdentityCheck, IdentityDocument, SignupAttempt, UsedChallenge, User

router = APIRouter(tags=["inscription"])
MAX_UPLOAD = 5 * 1024 * 1024
IMAGE_TYPES = {"image/jpeg", "image/png"}
MAX_FAILED_PER_CIN, MAX_FAILED_PER_IP, WINDOW_MINUTES = 5, 20, 30  # essais ratés par fenêtre de 30 minutes (IP plus large : réseau partagé)
CHALLENGE_MINUTES = 5

_service = OpenCVFaceService()


def get_identity_agent() -> IdentityAgent:
    return IdentityAgent(_service)


class SignupFields(BaseModel):
    email: str = Field(pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$", max_length=254)
    password: str = Field(min_length=10, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)
    cin: str = Field(max_length=20)

    @field_validator("cin")
    @classmethod
    def _cin(cls, v):
        return clean_cin(v)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _keys(cin: str, request: Request) -> list[tuple[str, int]]:
    ip = request.client.host if request.client else "unknown"
    return [(security.fingerprint("cin:" + cin), MAX_FAILED_PER_CIN), (security.fingerprint("ip:" + ip), MAX_FAILED_PER_IP)]


def _blocked(db: Session, keys: list[tuple[str, int]]) -> bool:
    since = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MINUTES)
    for key, limit in keys:
        n = db.scalar(select(func.count()).select_from(SignupAttempt).where(
            SignupAttempt.key_hash == key, SignupAttempt.success.is_(False), SignupAttempt.created_at > since))
        if n >= limit:
            return True
    return False


@router.get("/auth/signup/challenge")
def challenge():
    steps = liveness.make_steps()
    token = security.make_purpose_token("signup", CHALLENGE_MINUTES, steps=steps, jti=secrets.token_hex(16))
    return {"token": token, "steps": [{"key": s, "text": liveness.STEP_TEXT[s]} for s in steps]}


async def _read(file: UploadFile, label: str) -> bytes:
    if file.content_type not in IMAGE_TYPES:
        raise HTTPException(422, f"{label} : formats acceptés JPG ou PNG.")
    data = await file.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, f"{label} : fichier trop gros (5 Mo maximum).")
    return data


@router.post("/auth/signup", status_code=201)
async def signup(request: Request, email: str = Form(...), password: str = Form(...), full_name: str = Form(...),
                 cin: str = Form(...), token: str = Form(...), cin_image: UploadFile = File(...),
                 frames: list[UploadFile] = File(...), db: Session = Depends(get_session),
                 agent: IdentityAgent = Depends(get_identity_agent)):
    try:
        fields = SignupFields(email=email, password=password, full_name=full_name, cin=cin)
    except ValidationError as error:
        msg = error.errors()[0]["msg"].replace("Value error, ", "")
        raise HTTPException(422, msg) from error

    keys = _keys(fields.cin, request)
    if _blocked(db, keys):
        raise HTTPException(429, f"Trop d'essais. Réessayez dans {WINDOW_MINUTES} minutes.")
    email_norm = fields.email.strip().lower()
    if db.scalar(select(User).where(User.email == email_norm)):
        raise HTTPException(409, "Cette adresse est déjà utilisée.")
    cin_hash = security.fingerprint(fields.cin)
    if db.scalar(select(User).where(User.cin_hash == cin_hash)):
        raise HTTPException(409, "Un compte existe déjà avec cette CIN.")

    claims = security.read_purpose_token(token, "signup")
    if not claims or db.get(UsedChallenge, claims["jti"]):
        raise HTTPException(422, "Le défi webcam a expiré ou a déjà servi : recommencez l'étape caméra.")
    steps: list[str] = claims["steps"]
    if len(frames) != len(steps):
        raise HTTPException(422, f"{len(steps)} images de la webcam sont attendues.")

    cin_bytes = await _read(cin_image, "CIN")
    frame_bytes = [await _read(f, f"Webcam {i}") for i, f in enumerate(frames, start=1)]
    db.add(UsedChallenge(jti=claims["jti"]))

    try:
        verdict = agent.verify(cin_bytes, frame_bytes, steps, fields.cin)
    except DetectorUnavailable as error:
        db.rollback()
        raise HTTPException(503, str(error)) from error

    if verdict.outcome != "verified":
        for key, _ in keys:
            db.add(SignupAttempt(key_hash=key, success=False))
        audit(db, None, "signup_refused", "identity")
        db.commit()  # les essais ratés doivent être comptés même si on répond une erreur
        return JSONResponse(status_code=422, content={
            "detail": "Vérification d'identité non validée. Recommencez avec de nouvelles images.",
            "reasons": verdict.reasons})

    user = User(email=email_norm, full_name=fields.full_name.strip(), role="candidate",
                password_hash=security.hash_password(fields.password), identity_status="verified",
                email_verified=not email_confirmation_required(),
                cin_hash=cin_hash, cin_enc=security.encrypt(fields.cin))
    db.add(user)
    db.flush()
    db.add(IdentityDocument(user_id=user.id, kind="cin", filename=cin_image.filename or "cin", media_type=cin_image.content_type or "", content=cin_bytes))
    center = steps.index("center")
    db.add(IdentityDocument(user_id=user.id, kind="profile_photo", filename="webcam.jpg", media_type=frames[center].content_type or "", content=frame_bytes[center]))
    db.add(IdentityCheck(user_id=user.id, agent=verdict.agent, outcome="verified", reasons=[], details=verdict.details))
    for key, _ in keys:
        db.add(SignupAttempt(key_hash=key, success=True))
    audit(db, user.id, "signup_verified")
    if email_confirmation_required():
        link = f"{mailer.APP_URL()}/?verify={security.make_purpose_token('verify_email', 24 * 60, sub=str(user.id))}"
        mailer.send_mail(user.email, "Confirmez votre adresse email",
                         f"Bonjour {user.full_name},\n\nVotre identité a été vérifiée. Confirmez votre email :\n{link}\n\nLe lien est valable 24 heures.")
    return {"message": "Identité vérifiée, compte créé.", "email_confirmation_required": email_confirmation_required()}
