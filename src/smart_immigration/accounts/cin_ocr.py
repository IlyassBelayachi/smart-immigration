"""Règle supplémentaire : le numéro de CIN saisi doit apparaître sur l'image envoyée (lecture OCR)."""
from __future__ import annotations

import re
from typing import Callable

# Confusions fréquentes de l'OCR entre lettres et chiffres.
_FIX = str.maketrans("OILSB", "01158")


def _clean(text: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def cin_in_text(cin: str, lines: list[str]) -> bool:
    blob = _clean(" ".join(lines))
    target = _clean(cin)
    return target in blob or target.translate(_FIX) in blob.translate(_FIX)


def read_lines(data: bytes) -> list[str] | None:
    """Lit le texte de l'image avec l'OCR du projet. None si l'OCR n'est pas installé."""
    try:
        import cv2
        import numpy as np
        from ..dossier.ocr import _engine  # moteur de Hicham, utilisé en lecture seule
    except ImportError:
        return None
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return []
    lines, _ = _engine()(img)
    return [text for _, text, _ in (lines or [])]


OcrReader = Callable[[bytes], "list[str] | None"]
