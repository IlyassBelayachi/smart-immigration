# Smart Immigration Process — PFA EMSI 2026-2027

Assistant de préparation d'un **permis d'études canadien** (agents IA, réponses sourcées sur les pages officielles IRCC, critères vérifiés par des règles claires, validation humaine).
Encadrante : Mme Kaoutar Karboub — 5IADO-G2 — Drief Richan & Ilyass Belayachi.

> L'assistant **ne décide rien** et **n'envoie rien** aux autorités : il aide à comprendre et à préparer.

## Par où commencer ? (lire dans cet ordre)

1. [`docs/01_VISION_PROJET.md`](docs/01_VISION_PROJET.md) — le projet de A à Z, en mots simples (avec glossaire)
2. [`docs/02_REPARTITION_TACHES.md`](docs/02_REPARTITION_TACHES.md) — qui fait quoi, règles pour ne pas se marcher dessus
3. [`docs/03_ROADMAP_ET_AVANCEMENT.md`](docs/03_ROADMAP_ET_AVANCEMENT.md) — où on va et où on en est (mis à jour chaque lundi)
4. [`CLAUDE.md`](CLAUDE.md) — le résumé destiné aux outils d'IA

## Démarrage rapide

```bash
python -m venv .venv && source .venv/bin/activate     # Windows : .venv\Scripts\activate
pip install -r requirements.txt
pytest -q                                               # 22 tests doivent passer
cd src && uvicorn smart_immigration.api:app --reload    # puis ouvrir http://127.0.0.1:8000/docs
```

Ouvrir `/demo/` pour le parcours de démonstration (question sourcée, verdicts du profil et checklist).
Dans `/docs` : `POST /ask` (question → réponse avec sources, ou refus), `POST /assess` (profil → verdicts)
et `POST /checklist` (profil → éléments à fournir ou à confirmer).

## Corpus réel (à faire sur votre ordinateur)

Le dépôt contient un **corpus d'amorçage** (`data/seed/`, 10 passages reformulés de 4 pages IRCC) pour que la démo tourne tout de suite.
Pour copier les vraies pages :

```bash
cd src && python -m smart_immigration.knowledge.ingest   # écrit data/corpus/chunks.jsonl (utilisé en priorité)
```

## Organisation du code (un dossier = un propriétaire)

| Dossier | Propriétaire |
|---|---|
| `src/smart_immigration/knowledge/`, `tests/knowledge/`, `data/sources.yaml`, `data/seed/`, `eval/knowledge/` | Personne 1 (Connaissance) |
| `src/smart_immigration/dossier/`, `tests/dossier/`, `rules/`, `data/synthetic/`, `eval/dossier/`, `frontend/` | Personne 2 (Dossier) |
| `src/smart_immigration/schemas.py`, `api.py`, `docs/`, `requirements.txt`, `.github/` | Les deux |

**Les règles officielles changent** (exemple : le montant à prouver a changé le 1er septembre 2026). Chaque règle porte son lien et sa date de lecture ; revérifier avant la démo finale.
