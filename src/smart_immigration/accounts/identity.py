"""Agent de vérification d'identité, utilisé À L'INSCRIPTION : le compte candidat n'est créé que si tout est validé.

Contrôles : CIN lisible avec un visage ; photo webcam nette avec un seul visage ; visage de face
(photo de face prise en direct) ; visage webcam = visage de la CIN ; numéro de CIN saisi retrouvé sur l'image (OCR, si disponible).
En cas de doute : on demande de recommencer (jamais de passage par le consultant).

LIMITES : une photo présentée devant la caméra pourrait passer ; ce n'est pas un test anti-fraude certifié.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from . import cin_ocr, liveness
from .face import FaceObs, FaceProblem, FaceService

THRESHOLD_CENTER = 0.363  # seuil cosinus recommandé pour SFace
THRESHOLD_TURNED = 0.25   # visage tourné : la ressemblance baisse naturellement


@dataclass
class IdentityVerdict:
    outcome: str  # verified | resubmit
    reasons: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    agent: str = "identity-agent-v1"


class IdentityAgent:
    def __init__(self, faces: FaceService, ocr: cin_ocr.OcrReader | None = cin_ocr.read_lines):
        self.faces = faces
        self.ocr = ocr

    def verify(self, cin_image: bytes, frames: list[bytes], steps: list[str], typed_cin: str) -> IdentityVerdict:
        reasons: list[str] = []
        details: dict = {"liveness": "single-live-capture"}

        if hashlib.sha256(cin_image).hexdigest() in {hashlib.sha256(f).hexdigest() for f in frames}:
            return IdentityVerdict("resubmit", ["La photo en direct ne doit pas être le fichier de la CIN : utilisez la caméra."], details)

        cin_obs: FaceObs | None = None
        try:
            cin_obs = self.faces.analyze(cin_image, "cin")
        except FaceProblem as problem:
            reasons.append(f"CIN : {problem}")

        observed: list[FaceObs | None] = []
        for i, frame in enumerate(frames, start=1):
            try:
                observed.append(self.faces.analyze(frame, "selfie"))
            except FaceProblem as problem:
                observed.append(None)
                reasons.append(f"Webcam, étape {i} : {problem}")

        if all(observed):
            reasons += liveness.check_poses(steps, [o.yaw for o in observed])
            if cin_obs is not None and not reasons:
                scores = [self.faces.similarity(cin_obs, o) for o in observed]
                details["similarity"] = [round(s, 3) for s in scores]
                for step, score in zip(steps, scores):
                    need = THRESHOLD_CENTER if step == "center" else THRESHOLD_TURNED
                    if score < need:
                        reasons.append("Le visage devant la caméra ne correspond pas assez à celui de la CIN.")
                        break

        if cin_obs is not None and self.ocr is not None:
            lines = self.ocr(cin_image)
            if lines is None:
                details["cin_number_check"] = "ocr_unavailable"
            elif cin_ocr.cin_in_text(typed_cin, lines):
                details["cin_number_check"] = "match"
            else:
                details["cin_number_check"] = "no_match"
                reasons.append("Le numéro de CIN saisi n'a pas été retrouvé sur l'image : vérifiez-le ou renvoyez une photo plus nette.")

        return IdentityVerdict("resubmit" if reasons else "verified", reasons, details)
