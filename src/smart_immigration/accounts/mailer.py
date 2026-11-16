"""Envoi d'emails. Sans SMTP_HOST, le message s'affiche dans la console du serveur (mode développement)."""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

log = logging.getLogger("smartimm.mail")
APP_URL = lambda: os.environ.get("APP_URL", "http://localhost:5173").rstrip("/")  # noqa: E731


def send_mail(to: str, subject: str, body: str) -> None:
    host = os.environ.get("SMTP_HOST")
    if not host:
        print(f"\n=== EMAIL (mode développement) ===\nÀ : {to}\nObjet : {subject}\n{body}\n==================================\n", flush=True)
        return
    msg = EmailMessage()
    msg["From"] = os.environ.get("SMTP_FROM", "no-reply@smart-immigration.local")
    msg["To"], msg["Subject"] = to, subject
    msg.set_content(body)
    with smtplib.SMTP(host, int(os.environ.get("SMTP_PORT", "587"))) as smtp:
        smtp.starttls()
        if os.environ.get("SMTP_USER"):
            smtp.login(os.environ["SMTP_USER"], os.environ.get("SMTP_PASSWORD", ""))
        smtp.send_message(msg)
