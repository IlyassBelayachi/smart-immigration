"""Assemblage de l'API et de l'interface minimale de demonstration.

Lancer (depuis le dossier src/) :  uvicorn smart_immigration.api:app --reload
Pour ajouter une route : la créer dans knowledge/routes.py ou dossier/routes.py (chacun son fichier).
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .accounts.routes import router as accounts_router
from .dossier.routes import router as dossier_router
from .knowledge.routes import router as knowledge_router

app = FastAPI(title="Smart Immigration Process", version="0.1.0")
app.include_router(knowledge_router)
app.include_router(dossier_router)
app.include_router(accounts_router)


@app.get("/", include_in_schema=False)
def demo_home() -> RedirectResponse:
    return RedirectResponse(url="/demo/")


app.mount(
    "/demo",
    StaticFiles(directory=Path(__file__).resolve().parents[2] / "frontend", html=True),
    name="demo",
)


# Interface React (Ilyass) : npm run build dans frontend-app/ puis http://127.0.0.1:8000/app/
_REACT_DIST = Path(__file__).resolve().parents[2] / "frontend-app" / "dist"
if _REACT_DIST.exists():
    app.mount("/app", StaticFiles(directory=_REACT_DIST, html=True), name="app")
