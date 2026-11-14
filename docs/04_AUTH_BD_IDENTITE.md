# 04 — Comptes, base de données et vérification d'identité (Ilyass)

Code : `src/smart_immigration/accounts/` · Tests : `tests/accounts/` (13 tests).

## Le scénario
1. **Le candidat crée un compte** → statut `pending_identity`.
2. Il envoie sa **photo de profil** et sa **photo de CIN** (`POST /identity/submit`).
3. **L'agent d'identité** (OpenCV) vérifie : image lisible, assez grande, nette, **un seul visage** sur chaque photo, visages assez semblables.
   - Tout va bien → `verified`.
   - **Doute** → `resubmit_requested` + raisons en français : le candidat renvoie des photos. Pas de refus définitif, pas de passage par le consultant.
4. Seul un candidat `verified` peut créer une **demande d'immigration** (`POST /requests`) ; les règles automatiques ajoutent une **recommandation** (Canada/études pour l'instant, sinon « non couvert : examen humain »).
5. **Le consultant examine les demandes** (`GET /consultant/requests`) et **décide** (`approved`, `rejected`, `needs_info`, avec motif obligatoire). Il ne vérifie jamais les comptes.

## Sécurité
Mots de passe argon2 ; session en cookie HttpOnly SameSite=Strict (8 h) ; blocage 15 min après 5 échecs ; compte consultant uniquement avec code d'invitation (`CONSULTANT_INVITE`) ; un candidat ne voit que ses demandes ; journal d'audit ; fichiers limités à JPG/PNG de 5 Mo.

## Limites à annoncer honnêtement
- **Pas de test de « personne vivante »** : une photo d'une photo peut passer.
- La comparaison de visages par défaut est une **version de démonstration peu fiable** ; à remplacer par un vrai modèle (ex. OpenCV SFace) via l'interface `FaceMatcher`.
- Si le modèle de détection OpenCV est absent, l'API répond 503 et **ne valide jamais** un compte.
- Tests faits sur SQLite ; **PostgreSQL à tester** sur votre machine (`docker compose up -d`, puis `DATABASE_URL` dans `.env`).
- Photos stockées dans la base : acceptable pour la démo, à chiffrer pour un vrai usage (loi 09-08 / CNDP). Données fictives ou consenties uniquement.

## Lancer
`pip install -r requirements.txt` · `pytest -q` · `cd src && uvicorn smart_immigration.api:app --reload` → `/docs`
