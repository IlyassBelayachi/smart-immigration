"""Mots de passe (argon2) et sessions (jeton JWT dans un cookie HttpOnly)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import warnings
from pathlib import Path
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.fernet import Fernet, InvalidToken
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


# ---------- Identifiants sensibles (CIN, passeport) ----------
CIN_RE = re.compile(r"^[A-Z]{1,3}[0-9]{6,8}$")        # 1-3 lettres (région) + 6-8 chiffres
PASSPORT_RE = re.compile(r"^[A-Z0-9]{6,12}$")          # souple : pas de format officiel vérifié


def normalize_id(value: str) -> str:
    return re.sub(r"[\s\-]", "", value).upper()


KEY_FILE = Path(__file__).resolve().parents[3] / "data" / "private" / "data.key"


def _material() -> bytes:
    """Clé de chiffrement : variable DATA_ENCRYPTION_KEY, sinon fichier local créé une fois (jamais sur GitHub).
    Perdre cette clé = CIN et passeports illisibles ; la sauvegarder avec la base."""
    env = os.environ.get("DATA_ENCRYPTION_KEY")
    if env:
        return env.encode()
    if not KEY_FILE.exists():
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(secrets.token_urlsafe(48))
    return KEY_FILE.read_text().strip().encode()


def _fernet() -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(b"enc:" + _material()).digest()))


def encrypt(value: str) -> str:
    return _fernet().encrypt(value.encode()).decode()


def decrypt(token: str) -> str | None:
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return None


def fingerprint(value: str) -> str:
    """Empreinte non réversible : sert à refuser deux comptes avec la même CIN."""
    return hmac.new(hashlib.sha256(b"hash:" + _material()).digest(), value.encode(), hashlib.sha256).hexdigest()


def mask(value: str) -> str:
    return "*" * max(len(value) - 3, 0) + value[-3:]
