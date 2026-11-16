"""Contrôle « en direct » : UNE photo prise par la webcam, visage de face, au moment de l'inscription.

Le défi (jeton signé à usage unique, valable 5 min) empêche de rejouer une ancienne requête.
`yaw` = décalage horizontal du nez par rapport au milieu des yeux, divisé par l'écart entre les yeux (0 = de face).
LIMITE : ce n'est pas un test anti-fraude certifié (une photo présentée devant la caméra pourrait passer).
"""
from __future__ import annotations

CENTER_MAX = 0.35  # tolérant : il suffit de regarder à peu près la caméra

STEP_TEXT = {"center": "Regardez droit vers la caméra"}


def make_steps() -> list[str]:
    return ["center"]


def check_poses(steps: list[str], yaws: list[float]) -> list[str]:
    return [
        "Regardez droit vers la caméra, le visage de face."
        for step, yaw in zip(steps, yaws)
        if step == "center" and abs(yaw) > CENTER_MAX
    ]
