"""Confirmation de l'email et mot de passe oublié (liens envoyés par email ; en développement : affichés dans la console)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import mailer, security
from .common import audit, email_confirmation_required
from .db import get_session
from .models import User

router = APIRouter(tags=["comptes"])


class TokenBody(BaseModel):
    token: str = Field(max_length=2000)


class EmailBody(BaseModel):
    email: str = Field(max_length=254)


class ResetBody(TokenBody):
    password: str = Field(min_length=10, max_length=128)


def _by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email.strip().lower()))


@router.post("/auth/verify-email")
def verify_email(body: TokenBody, db: Session = Depends(get_session)):
    claims = security.read_purpose_token(body.token, "verify_email")
    user = db.get(User, int(claims["sub"])) if claims else None
    if user is None:
        raise HTTPException(400, "Lien invalide ou expiré. Demandez un nouvel email de confirmation.")
    user.email_verified = True
    audit(db, user.id, "email_verified")
    return {"message": "Adresse email confirmée. Vous pouvez vous connecter."}


@router.post("/auth/resend-confirmation", status_code=202)
def resend_confirmation(body: EmailBody, db: Session = Depends(get_session)):
    user = _by_email(db, body.email)
    if user and not user.email_verified and email_confirmation_required():
        link = f"{mailer.APP_URL()}/?verify={security.make_purpose_token('verify_email', 24 * 60, sub=str(user.id))}"
        mailer.send_mail(user.email, "Confirmez votre adresse email", f"Confirmez votre email :\n{link}")
    return {"message": "Si un compte existe, un email a été envoyé."}  # même réponse dans tous les cas


@router.post("/auth/forgot-password", status_code=202)
def forgot_password(body: EmailBody, db: Session = Depends(get_session)):
    user = _by_email(db, body.email)
    if user:
        token = security.make_purpose_token("reset", 60, sub=str(user.id), pf=security.password_fingerprint(user.password_hash))
        mailer.send_mail(user.email, "Réinitialisation du mot de passe",
                         f"Pour choisir un nouveau mot de passe (lien valable 1 heure) :\n{mailer.APP_URL()}/?reset={token}\n\n"
                         "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message.")
        audit(db, user.id, "password_reset_requested")
    return {"message": "Si un compte existe, un email a été envoyé."}


@router.post("/auth/reset-password")
def reset_password(body: ResetBody, db: Session = Depends(get_session)):
    claims = security.read_purpose_token(body.token, "reset")
    user = db.get(User, int(claims["sub"])) if claims else None
    if user is None or claims.get("pf") != security.password_fingerprint(user.password_hash):
        raise HTTPException(400, "Lien invalide, expiré ou déjà utilisé.")
    user.password_hash = security.hash_password(body.password)
    user.failed_attempts, user.locked_until = 0, None
    audit(db, user.id, "password_reset")
    return {"message": "Mot de passe modifié. Vous pouvez vous connecter."}
