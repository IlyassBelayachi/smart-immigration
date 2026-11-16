"""Détection et comparaison de visages (OpenCV YuNet + SFace).

Les deux fichiers modèles (petits, gratuits) se téléchargent une fois : `python scripts/download_face_models.py`.
Dossier par défaut : `models/` à la racine du projet (ou variable FACE_MODELS_DIR). Jamais envoyés sur GitHub.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any, Protocol

import cv2
import numpy as np

MIN_SIDE = {"selfie": 240, "cin": 400}  # pixels
MIN_SHARPNESS = 40.0                      # variance du Laplacien
MIN_SCORE = 0.8                           # confiance du détecteur
YUNET = "face_detection_yunet_2023mar.onnx"
SFACE = "face_recognition_sface_2021dec.onnx"
MODELS_DIR = Path(os.environ.get("FACE_MODELS_DIR") or Path(__file__).resolve().parents[3] / "models")


class DetectorUnavailable(RuntimeError):
    """Modèles absents : on ne valide jamais un compte dans ce cas."""


class FaceProblem(Exception):
    """Image inutilisable (floue, pas de visage...). Le message est montré au candidat."""


@dataclass
class FaceObs:
    embedding: Any
    yaw: float
    sharpness: float


class FaceService(Protocol):
    def analyze(self, data: bytes, kind: str) -> FaceObs: ...
    def similarity(self, a: FaceObs, b: FaceObs) -> float: ...


class OpenCVFaceService:
    # Seuil cosinus recommandé par OpenCV pour SFace : 0.363
    def __init__(self, models_dir: Path | None = None):
        self.dir = Path(models_dir or MODELS_DIR)
        self._lock = Lock()
        self._det = self._rec = None

    def _load(self):
        if self._det is None:
            det_path, rec_path = self.dir / YUNET, self.dir / SFACE
            if not det_path.exists() or not rec_path.exists():
                raise DetectorUnavailable(
                    "Modèles de visage absents. Lancez : python scripts/download_face_models.py"
                )
            self._det = cv2.FaceDetectorYN.create(str(det_path), "", (320, 320), MIN_SCORE, 0.3, 5000)
            self._rec = cv2.FaceRecognizerSF.create(str(rec_path), "")

    def analyze(self, data: bytes, kind: str) -> FaceObs:
        with self._lock:
            self._load()  # échoue tout de suite (DetectorUnavailable) si les modèles manquent
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR) if data else None
        if img is None:
            raise FaceProblem("fichier illisible : envoyez une image JPG ou PNG.")
        h, w = img.shape[:2]
        if min(h, w) < MIN_SIDE[kind]:
            raise FaceProblem(f"image trop petite (minimum {MIN_SIDE[kind]} pixels de côté).")
        sharp = float(cv2.Laplacian(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
        if sharp < MIN_SHARPNESS:
            raise FaceProblem("image floue : refaites la photo avec plus de lumière, sans bouger.")
        with self._lock:
            self._load()
            self._det.setInputSize((w, h))
            _, faces = self._det.detect(img)
            if faces is None or len(faces) == 0:
                raise FaceProblem("aucun visage détecté.")
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            # Webcam : un seul visage. CIN : on garde le plus grand (la CIN peut avoir une petite photo secondaire).
            if kind == "selfie" and len(faces) > 1 and faces[1][2] * faces[1][3] > 0.25 * faces[0][2] * faces[0][3]:
                raise FaceProblem("plusieurs visages détectés : une seule personne face à la caméra.")
            face = faces[0]
            aligned = self._rec.alignCrop(img, face)
            emb = self._rec.feature(aligned)
        re_x, le_x, nose_x = float(face[4]), float(face[6]), float(face[8])
        eye_dist = max(abs(le_x - re_x), 1.0)
        return FaceObs(embedding=emb, yaw=(nose_x - (re_x + le_x) / 2) / eye_dist, sharpness=sharp)

    def similarity(self, a: FaceObs, b: FaceObs) -> float:
        with self._lock:
            self._load()
            return float(self._rec.match(a.embedding, b.embedding, cv2.FaceRecognizerSF_FR_COSINE))
