"""Agent de vérification d'identité (photo de profil + photo de la CIN, OpenCV).

Règle : en cas de doute, l'agent demande de renvoyer une photo ("resubmit"). Il ne refuse jamais définitivement
et il ne transmet pas les cas douteux au consultant.

LIMITES (à annoncer honnêtement) :
- pas de test de "personne vivante" : une photo d'une photo peut passer ;
- la comparaison de visages par défaut (`HistogramFaceMatcher`) est un comparateur de démonstration, peu fiable ;
  pour un vrai usage, brancher un modèle (ex. OpenCV SFace) via l'interface `FaceMatcher`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Protocol

import cv2
import numpy as np

MIN_SIDE = 200          # pixels
MIN_SHARPNESS = 60.0    # variance du Laplacien : en dessous, image floue
MATCH_THRESHOLD = 0.45  # seuil du comparateur de démonstration

Box = tuple[int, int, int, int]  # x, y, w, h
Detector = Callable[[np.ndarray], list[Box]]


class FaceMatcher(Protocol):
    name: str

    def similarity(self, face_a: np.ndarray, face_b: np.ndarray) -> float: ...


@dataclass
class IdentityVerdict:
    outcome: str  # verified | resubmit
    reasons: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)
    agent: str = "identity-agent-v0"


class DetectorUnavailable(RuntimeError):
    """Le détecteur de visage n'est pas utilisable : on ne valide jamais un compte dans ce cas."""


def haar_detector(image: np.ndarray) -> list[Box]:
    if not hasattr(cv2, "CascadeClassifier"):
        raise DetectorUnavailable("OpenCV 4.x requis pour la détection de visage.")
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    if cascade.empty():
        raise DetectorUnavailable("Modèle de détection de visage introuvable (installer opencv-python 4.x).")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return [tuple(int(v) for v in b) for b in cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))]


class HistogramFaceMatcher:
    """Comparateur de DÉMONSTRATION (corrélation de visages normalisés). Pas fiable."""
    name = "demo-histogram-matcher"

    def similarity(self, face_a: np.ndarray, face_b: np.ndarray) -> float:
        def prep(f: np.ndarray) -> np.ndarray:
            g = cv2.equalizeHist(cv2.cvtColor(cv2.resize(f, (100, 100)), cv2.COLOR_BGR2GRAY))
            return g.astype(np.float32)
        a, b = prep(face_a), prep(face_b)
        a, b = a - a.mean(), b - b.mean()
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        return float((a * b).sum() / denom) if denom else 0.0


def _decode(data: bytes) -> np.ndarray | None:
    arr = np.frombuffer(data, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR) if arr.size else None


class IdentityAgent:
    def __init__(self, detector: Detector = haar_detector, matcher: FaceMatcher | None = None):
        self.detector = detector
        self.matcher = matcher or HistogramFaceMatcher()

    def _check_image(self, label: str, data: bytes, reasons: list[str], details: dict):
        img = _decode(data)
        if img is None:
            reasons.append(f"{label} : fichier illisible, renvoyez une image JPG ou PNG.")
            return None
        h, w = img.shape[:2]
        if min(h, w) < MIN_SIDE:
            reasons.append(f"{label} : image trop petite (minimum {MIN_SIDE} px).")
            return None
        sharp = float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        details[f"{label}_sharpness"] = round(sharp, 1)
        if sharp < MIN_SHARPNESS:
            reasons.append(f"{label} : image floue, renvoyez une photo plus nette.")
            return None
        faces = self.detector(img)
        details[f"{label}_faces"] = len(faces)
        if len(faces) != 1:
            reasons.append(f"{label} : {len(faces)} visage(s) détecté(s), un seul visage bien visible est attendu.")
            return None
        x, y, fw, fh = faces[0]
        return img[y:y + fh, x:x + fw]

    def verify(self, profile_photo: bytes, cin_image: bytes) -> IdentityVerdict:
        reasons: list[str] = []
        details: dict = {"matcher": self.matcher.name, "liveness": "not_checked"}
        face_p = self._check_image("photo_profil", profile_photo, reasons, details)
        face_c = self._check_image("cin", cin_image, reasons, details)
        if reasons or face_p is None or face_c is None:
            return IdentityVerdict("resubmit", reasons, details)
        score = self.matcher.similarity(face_p, face_c)
        details["similarity"] = round(score, 3)
        if score < MATCH_THRESHOLD:
            return IdentityVerdict("resubmit", ["Le visage de la photo ne correspond pas assez à celui de la CIN : renvoyez des photos plus nettes et de face."], details)
        return IdentityVerdict("verified", [], details)
