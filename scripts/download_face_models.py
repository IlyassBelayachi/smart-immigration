"""Télécharge les deux petits modèles de visage d'OpenCV dans le dossier models/ (une seule fois)."""
import sys
import urllib.request
from pathlib import Path

BASE = "https://github.com/opencv/opencv_zoo/raw/main/models"
FILES = {
    "face_detection_yunet_2023mar.onnx": f"{BASE}/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx": f"{BASE}/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}
dest = Path(__file__).resolve().parents[1] / "models"
dest.mkdir(exist_ok=True)
for name, url in FILES.items():
    target = dest / name
    if target.exists() and target.stat().st_size > 100_000:
        print("déjà présent :", name)
        continue
    print("téléchargement :", name)
    urllib.request.urlretrieve(url, target)
    if target.stat().st_size < 100_000:  # une page d'erreur, pas un modèle
        target.unlink()
        sys.exit(f"Échec : {name} n'a pas été téléchargé correctement. Vérifiez la connexion et recommencez.")
print("Modèles prêts dans", dest)
