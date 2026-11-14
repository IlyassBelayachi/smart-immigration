# Smart Immigration Process Using Autonomous AI Agents

PFA : cadrage métier et préparation des données. Prototype gratuit local, sans API payante.

- docs/metier.md : règles validées et choix proposés.
- docs/strategie-ml.md : tâches, données et évaluation.
- data/destinations.csv : périmètre géographique initial ; aucune exigence de visa implicite.
- data/exigences.csv : structure vide pour les exigences sourcées.

Les pays du catalogue ne représentent pas des partenariats réels. Aucun modèle n'est encore entraîné. Les informations absentes ne valent pas absence d'exigence.

## Lancer le portail Candidat et Consultant

Le portail est le point d’entrée. L’onglet **Destinations** permet de chercher
un pays et de le sélectionner dans le formulaire. L’onglet **Simulation**
reprend les quotas, la file FIFO, la conservation et les notifications d’Atlas
avec le compte candidat du portail. Les demandes simulées sont stockées dans
le navigateur. Les candidatures et pièces examinées par les consultants
restent dans SQLite. Les anciens dossiers locaux d’Atlas restent dans le
stockage de leur adresse d’origine.

Les tests de la simulation se lancent depuis la racine avec
`node platform/test.cjs`. Si l’ancien serveur Atlas est utilisé, sa page
d’accueil redirige vers le portail.

Dans PowerShell, depuis la racine de PFA_5, avec Python 3.11 ou plus récent :

```powershell
cd portail-etudes
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m uvicorn smart_immigration.api:app --app-dir src --host 127.0.0.1 --port 8001
```

Ouvrir le [portail de démonstration](http://127.0.0.1:8001/demo/).
Pour permettre l'inscription d'un consultant fictif, définir
`IMMIGRATION_CONSULTANT_INVITE` dans le terminal du portail avant son démarrage
et saisir la même valeur dans le formulaire Consultant.

Le portail évalue les conditions documentées pour Canada–Études. Une
information manquante est signalée comme « À confirmer ». Le catalogue Atlas
et le formulaire multi-pays sont disponibles. Le classement personnalisé des
pays reste à développer.
