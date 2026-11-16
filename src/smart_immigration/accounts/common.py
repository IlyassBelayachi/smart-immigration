"""Éléments partagés par les routes de comptes."""
from __future__ import annotations

import os

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from . import security
from .db import get_session
from .models import AuditLog, User

DUMMY_HASH = security.hash_password("dummy-password-for-timing")


def email_confirmation_required() -> bool:
    return os.environ.get("REQUIRE_EMAIL_CONFIRMATION", "1") != "0"


def audit(db: Session, user_id: int | None, action: str, detail: str = "") -> None:
    db.add(AuditLog(user_id=user_id, action=action, detail=detail))


def public(u: User) -> dict:
    cin = security.decrypt(u.cin_enc) if u.cin_enc else None
    return {"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role,
            "identity_status": u.identity_status if u.role == "candidate" else None,
            "cin_masked": security.mask(cin) if cin else None, "has_passport": bool(u.passport_enc)}


def clean_cin(value: str) -> str:
    cin = security.normalize_id(value)
    if not security.CIN_RE.match(cin):
        raise ValueError("CIN invalide : 1 à 3 lettres suivies de 6 à 8 chiffres (ex. AB123456).")
    return cin


def clean_passport(value: str) -> str:
    passport = security.normalize_id(value)
    if not security.PASSPORT_RE.match(passport):
        raise ValueError("Passeport invalide : 6 à 12 lettres ou chiffres, sans symboles.")
    return passport


def start_session(response: Response, user: User) -> None:
    response.set_cookie(security.COOKIE, security.make_token(user.id, user.role), httponly=True,
                        samesite="strict", max_age=security.SESSION_HOURS * 3600)


def current_user(request: Request, db: Session = Depends(get_session)) -> User:
    payload = security.read_token(request.cookies.get(security.COOKIE, ""))
    user = db.get(User, int(payload["sub"])) if payload and payload.get("sub") else None
    if user is None:
        raise HTTPException(401, "Connectez-vous pour continuer.")
    return user


def require(role: str):
    def dep(user: User = Depends(current_user)) -> User:
        if user.role != role:
            raise HTTPException(403, "Action réservée à un autre type de compte.")
        return user
    return dep
