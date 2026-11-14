"""Mots de passe (argon2) et sessions (jeton JWT dans un cookie HttpOnly)."""
from __future__ import annotations

import os
import secrets
import warnings
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

COOKIE = "smartimm_session"
SESSION_HOURS = 8
MAX_FAILED = 5
LOCK_MINUTES = 15

_hasher = PasswordHasher()
_secret: str | None = None


def _jwt_secret() -> str:
    global _secret
    if _secret is None:
        _secret = os.environ.get("JWT_SECRET", "")
        if not _secret:
            warnings.warn("JWT_SECRET absent : secret aléatoire (les sessions sautent au redémarrage).")
            _secret = secrets.token_urlsafe(32)
    return _secret


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except VerifyMismatchError:
        return False


def make_token(user_id: int, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    return jwt.encode({"sub": str(user_id), "role": role, "exp": exp}, _jwt_secret(), algorithm="HS256")


def read_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
