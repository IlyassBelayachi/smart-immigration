"""Assemblage de l'API et de l'interface minimale de demonstration.

Lancer (depuis le dossier src/) :  uvicorn smart_immigration.api:app --reload
Pour ajouter une route : la créer dans knowledge/routes.py ou dossier/routes.py (chacun son fichier).
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .dossier.routes import router as dossier_router
from .knowledge.routes import router as knowledge_router

app = FastAPI(title="Smart Immigration Process", version="0.1.0")
app.include_router(knowledge_router)
app.include_router(dossier_router)


@app.get("/", include_in_schema=False)
def demo_home() -> RedirectResponse:
    return RedirectResponse(url="/demo/")


app.mount(
    "/demo",
    StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True),
    name="demo",
)
