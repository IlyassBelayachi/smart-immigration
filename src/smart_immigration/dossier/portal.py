"""Comptes et suivi des dossiers de la démonstration locale."""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/portal", tags=["dossier"])
DB_PATH = Path(__file__).resolve().parents[3] / "data" / "private" / "portal.sqlite3"
COOKIE = "immigration_session"
SESSION_SECONDS = 8 * 60 * 60


@contextmanager
def database():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    try:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
                role TEXT NOT NULL, salt TEXT NOT NULL, password TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY, account_id INTEGER NOT NULL, expires INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY, candidate_id INTEGER UNIQUE NOT NULL,
                consultant_id INTEGER, status TEXT NOT NULL, payload TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS case_events (
                id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL, author_id INTEGER NOT NULL,
                action TEXT NOT NULL, message TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS account_identity (
                account_id INTEGER PRIMARY KEY, cin TEXT NOT NULL, passport TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS intake_drafts (
                account_id INTEGER PRIMARY KEY, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS case_files (
                id INTEGER PRIMARY KEY, case_id INTEGER NOT NULL, kind TEXT NOT NULL,
                filename TEXT NOT NULL, media_type TEXT NOT NULL, content BLOB NOT NULL
            );
        """)
        with db:
            yield db
    finally:
        db.close()


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=10, max_length=128)
    role: Literal["candidate", "consultant"]


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=80)
    invitation: str = Field(default="", max_length=128)
    cin: str | None = Field(default=None, pattern=r"^DEMO-[A-Z0-9]{4,16}$")
    passport: str | None = Field(default=None, pattern=r"^DEMO-[A-Z0-9]{4,16}$")


class CaseAction(BaseModel):
    action: Literal["request_changes", "assign", "complete", "note", "approve_transmission"]
    message: str = Field(default="", max_length=2000)
    consultant_id: int | None = None


def _digest(password: str, salt: str) -> str:
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1).hex()


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def current_account(request: Request) -> dict:
    token = request.cookies.get(COOKIE, "")
    with database() as db:
        account = db.execute("""
            SELECT a.id, a.name, a.email, a.role FROM accounts a
            JOIN sessions s ON a.id = s.account_id
            WHERE s.token = ? AND s.expires > ?
        """, (_token_digest(token), int(time.time()))).fetchone()
    if account is None:
        raise HTTPException(401, "Connectez-vous pour continuer.")
    return dict(account)


@router.post("/signup", status_code=201)
def signup(body: Registration):
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Indiquez votre nom.")
    if (body.cin is None) != (body.passport is None):
        raise HTTPException(422, "Renseignez les deux identifiants fictifs.")
    if body.role == "consultant":
        invitation = os.environ.get("IMMIGRATION_CONSULTANT_INVITE", "")
        if not invitation or not hmac.compare_digest(invitation.encode(), body.invitation.encode()):
            raise HTTPException(403, "Un code d’invitation valide est requis pour créer un compte consultant.")
    salt = secrets.token_hex(16)
    try:
        with database() as db:
            cursor = db.execute("INSERT INTO accounts (email, name, role, salt, password) VALUES (?, ?, ?, ?, ?)",
                       (body.email.lower(), name, body.role, salt, _digest(body.password, salt)))
            if body.cin is not None:
                db.execute("INSERT INTO account_identity VALUES (?, ?, ?)", (cursor.lastrowid, body.cin, body.passport))
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "Cette adresse est déjà utilisée.") from error
    return {"message": "Compte créé. Vous pouvez vous connecter."}


@router.post("/signin")
def signin(body: Credentials, request: Request, response: Response):
    with database() as db:
        account = db.execute("SELECT * FROM accounts WHERE email = ?", (body.email.lower(),)).fetchone()
        digest = _digest(body.password, account["salt"] if account else "0" * 32)
        if not account or account["role"] != body.role or not hmac.compare_digest(digest, account["password"]):
            raise HTTPException(401, "Adresse, mot de passe ou espace incorrect.")
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        previous = request.cookies.get(COOKIE, "")
        db.execute("DELETE FROM sessions WHERE expires <= ? OR token = ?", (now, _token_digest(previous)))
        db.execute("INSERT INTO sessions VALUES (?, ?, ?)", (_token_digest(token), account["id"], now + SESSION_SECONDS))
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=request.url.scheme == "https",
                        max_age=SESSION_SECONDS)
    return {key: account[key] for key in ("id", "email", "name", "role")}


@router.post("/signout", status_code=204)
def signout(request: Request, response: Response):
    with database() as db:
        db.execute("DELETE FROM sessions WHERE token = ?", (_token_digest(request.cookies.get(COOKIE, "")),))
    response.delete_cookie(COOKIE)


@router.get("/me")
def me(account: dict = Depends(current_account)):
    return account


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)


@router.patch("/me")
def update_profile(body: ProfileUpdate, account: dict = Depends(current_account)):
    name = body.name.strip()
    if not name:
        raise HTTPException(422, "Indiquez votre nom.")
    with database() as db:
        db.execute("UPDATE accounts SET name = ? WHERE id = ?", (name, account["id"]))
    return {**account, "name": name}


@router.get("/cases")
def cases(account: dict = Depends(current_account)):
    with database() as db:
        query = """
            SELECT c.*, a.name AS candidate, b.name AS consultant FROM cases c
            JOIN accounts a ON a.id = c.candidate_id
            LEFT JOIN accounts b ON b.id = c.consultant_id
        """
        scope = "c.candidate_id = ?" if account["role"] == "candidate" else "(c.consultant_id = ? OR c.consultant_id IS NULL)"
        rows = db.execute(query + " WHERE " + scope + " ORDER BY c.updated_at DESC", (account["id"],)).fetchall()
        consultants = []
        if account["role"] == "consultant":
            consultants = [dict(row) for row in db.execute(
                "SELECT id, name FROM accounts WHERE role = 'consultant' ORDER BY name"
            )]
        return {"cases": [
            {**dict(row), "files": [dict(file) for file in db.execute(
                "SELECT id, kind, filename FROM case_files WHERE case_id = ? ORDER BY id", (row["id"],)
            )], "events": [dict(event) for event in db.execute("""
                SELECT e.action, e.message, e.created_at, a.name AS author FROM case_events e
                JOIN accounts a ON a.id = e.author_id
                WHERE e.case_id = ? AND (? = 'consultant' OR e.action <> 'note') ORDER BY e.id
            """, (row["id"], account["role"]))]} for row in rows
        ], "consultants": consultants}


def submit_case(account: dict, payload: str, files: list[tuple[str, str, str, bytes]] | None = None):
    if account["role"] != "candidate":
        raise HTTPException(403, "Cette action est réservée aux candidats.")
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        case = db.execute("SELECT id, status FROM cases WHERE candidate_id = ?", (account["id"],)).fetchone()
        if case is None:
            cursor = db.execute("INSERT INTO cases (candidate_id, status, payload) VALUES (?, 'submitted', ?)",
                                (account["id"], payload))
            case_id = cursor.lastrowid
        elif case["status"] == "needs_changes":
            case_id = case["id"]
            db.execute("UPDATE cases SET status = 'submitted', payload = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                       (payload, case_id))
        else:
            raise HTTPException(409, "Votre dossier a déjà été transmis.")
        if files:
            count = db.execute("SELECT COUNT(*) FROM case_files WHERE case_id = ?", (case_id,)).fetchone()[0]
            if count + len(files) > 12:
                raise HTTPException(422, "Un dossier peut contenir jusqu’à douze pièces.")
            db.executemany(
                "INSERT INTO case_files (case_id, kind, filename, media_type, content) VALUES (?, ?, ?, ?, ?)",
                [(case_id, *file) for file in files],
            )
        db.execute("INSERT INTO case_events (case_id, author_id, action) VALUES (?, ?, 'submitted')",
                   (case_id, account["id"]))
        db.execute("DELETE FROM intake_drafts WHERE account_id = ?", (account["id"],))
    return {"id": case_id, "status": "submitted"}


@router.post("/cases/{case_id}/actions")
def review_case(case_id: int, body: CaseAction, account: dict = Depends(current_account)):
    if account["role"] != "consultant":
        raise HTTPException(403, "Cette action est réservée aux consultants.")
    with database() as db:
        db.execute("BEGIN IMMEDIATE")
        case = db.execute("SELECT * FROM cases WHERE id = ? AND (consultant_id = ? OR consultant_id IS NULL)",
                          (case_id, account["id"])).fetchone()
        if not case:
            raise HTTPException(404, "Dossier introuvable.")
        if case["status"] in {"completed", "ready_to_send"} or (
            body.action not in {"assign", "note"} and case["status"] != "submitted"
        ):
            raise HTTPException(409, "Cette action ne correspond pas à l’état du dossier.")
        message = body.message.strip()
        assignee = account["id"]
        status = case["status"]
        if body.action == "assign":
            target = db.execute("SELECT id, name FROM accounts WHERE id = ? AND role = 'consultant'",
                                (body.consultant_id,)).fetchone()
            if not target:
                raise HTTPException(422, "Choisissez un consultant.")
            assignee = target["id"]
            message = "Dossier attribué à " + target["name"]
        elif body.action == "request_changes":
            if not message:
                raise HTTPException(422, "Précisez le complément demandé.")
            status = "needs_changes"
        elif body.action == "approve_transmission":
            if not message:
                raise HTTPException(422, "Renseignez le motif de la décision.")
            status = "ready_to_send"
        elif body.action == "note":
            if not message:
                raise HTTPException(422, "Renseignez votre observation.")
        else:
            status = "completed"
        db.execute("UPDATE cases SET consultant_id = ?, status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (assignee, status, case_id))
        db.execute("INSERT INTO case_events (case_id, author_id, action, message) VALUES (?, ?, ?, ?)",
                   (case_id, account["id"], body.action, message))
    return {"status": status}
