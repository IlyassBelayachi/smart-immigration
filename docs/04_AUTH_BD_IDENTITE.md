# 04 — Comptes, base de données et vérification d'identité (Ilyass)

Code : `src/smart_immigration/accounts/` · Interface : `frontend-app/` · Tests : `tests/accounts/`.

## Scénario d'authentification

### Candidat — le compte n'est créé qu'APRÈS la vérification d'identité
1. **Informations** : nom, email, mot de passe (10 caractères min.), **CIN** (1 à 3 lettres + 6 à 8 chiffres, ex. `AB123456`).
2. **CIN** : envoi d'une photo ou d'un scan net du recto.
3. **Vérification en direct (webcam)** : une seule photo, prise en direct par la caméra (compte à rebours de 3 secondes, visage de face). Aucun geste à faire.
4. **L'agent d'identité** contrôle : CIN lisible avec un visage ; photo nette avec un seul visage, regardant la caméra ; visage webcam = visage de la CIN ; **numéro de CIN saisi retrouvé sur l'image (OCR)** ; photo en direct différente du fichier de la CIN.
5. **Tout est bon** → le compte est créé (identité « vérifiée »), un email de confirmation est envoyé. **Sinon aucun compte n'est créé** : raisons affichées, nouvel essai avec un nouveau défi (un défi ne sert qu'une fois).
6. **Confirmation de l'email** (lien) puis connexion. Le **passeport est facultatif** et s'ajoute plus tard (profil ou demande).

### Consultant
Création avec **code d'invitation** (pas de CIN, pas de vérification d'identité), puis connexion. Il **examine les demandes d'immigration et décide** (approuver / compléter / refuser, motif obligatoire). Il ne vérifie jamais les comptes : c'est l'agent.

### Règles communes
- Mot de passe argon2 ; session 8 h en cookie HttpOnly ; blocage 15 min après 5 mots de passe faux.
- **Essais d'identité** : 5 échecs par CIN (ou 20 par adresse réseau) par fenêtre de 30 min, puis blocage temporaire.
- **Mot de passe oublié** : lien par email valable 1 h, utilisable une seule fois ; même réponse que le compte existe ou non.
- CIN et passeport **chiffrés** en base ; une CIN = un seul compte ; seul le masque (`*****456`) est renvoyé.
- Un défi webcam ne sert qu'une fois (anti-rejeu) et expire après 5 min.
- Photos (CIN + image webcam de face) conservées en base ; journal d'audit.

## Emails
Sans `SMTP_HOST`, les emails **s'affichent dans la console du serveur** (mode développement) : copier le lien. Pour un vrai envoi : `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`. `APP_URL` = adresse de l'interface (par défaut `http://localhost:5173`). `REQUIRE_EMAIL_CONFIRMATION=0` désactive la confirmation (tests).

## Modèles de visage (obligatoires pour la vérification réelle)
`python scripts/download_face_models.py` télécharge OpenCV YuNet (détection) et SFace (comparaison) dans `models/` (ignoré par Git). Sans eux, l'inscription répond « 503 » et **ne crée jamais de compte**.

## Limites à annoncer honnêtement
- Une seule photo en direct ne prouve pas que la personne est vivante : **une photo ou une vidéo présentée devant la caméra pourrait tromper** le contrôle. Ce n'est pas un test anti-fraude certifié.
- Les seuils (ressemblance 0,363, référence OpenCV ; visage de face 0,35) sont à **ajuster avec de vraies captures** ; ils sont dans `identity.py` et `liveness.py`.
- La règle OCR dépend de la qualité de lecture de la CIN ; si l'OCR n'est pas installé elle est ignorée (notée dans le journal).
- Format de CIN tiré d'une seule source (à confirmer sur une vraie CIN) ; format du passeport non vérifié (validation souple).
- Tests faits sur SQLite et avec de faux modèles de visage ; **PostgreSQL et modèles réels à tester** sur votre machine.
- Photos stockées en base : acceptable pour la démo, à chiffrer pour un vrai usage (loi 09-08 / CNDP). Données fictives ou consenties uniquement.

## Lancer
- Backend : `cd src && uvicorn smart_immigration.api:app --reload`
- Interface (dev) : `cd frontend-app && npm install && npm run dev` → http://localhost:5173
- Interface servie par l'API : `cd frontend-app && npm run build` → http://127.0.0.1:8000/app/
- Tests : `pytest -q`

## À faire plus tard
« Complément demandé » (le candidat modifie sa demande) · visibilité / attribution des demandes (décision de Hicham) · chiffrement des photos · vrai test anti-fraude.
