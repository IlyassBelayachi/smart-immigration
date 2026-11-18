# Livrables P2 — Dossier Canada–Études

## Démonstration reproductible

Depuis la racine du projet sous Windows, lancer `powershell -ExecutionPolicy Bypass -File .\lancer-demo-p2.ps1`. Le script prépare l’environnement si nécessaire, affiche le lien local et une invitation consultant pour la session. Ajouter `-Install` pour réinstaller les dépendances dans un environnement existant. Le service écoute uniquement sur la boucle locale.

1. Ouvrir `/demo/` et créer deux comptes fictifs dans deux sessions navigateur. Utiliser l’invitation affichée dans le terminal pour le consultant.
2. Depuis la démo, poser la question « Is the biometrics fee required when I submit? » et ouvrir la source citée.
3. Choisir Ontario, licence, lettre d’acceptation et PAL disponibles, une personne, le 18 novembre 2026, 12 000 CAD de scolarité et 1 500 CAD de transport. Laisser les fonds déclarés vides pour illustrer la lecture de pièce.
4. Charger les trois spécimens d’acceptation, de relevé et de financement. Lire les champs, corriger le relevé selon son original, confirmer et demander le rapport. Le justificatif confirmé indique 45 000 CAD. La checklist distingue les pièces déclarées et les points à vérifier.
5. Transmettre le dossier. Dans l’espace consultant, ouvrir la checklist, vérifier ses sources et enregistrer une décision motivée. Revenir côté candidat pour vérifier le statut.
6. Rejouer en changeant le total déclaré ou le nom d’un des spécimens pour montrer le blocage et la reprise après correction.

Le test `tests/dossier/test_portal.py` vérifie le parcours par API, de la question sourcée jusqu’à la décision affichée côté candidat.

## Chapitre de mémoire — Documents et règles

Le lecteur transforme des spécimens TXT ou PDF en champs associés à une pièce et à une page. Le lecteur extrait le texte natif quand il est disponible et lance l’OCR pour les pages scannées. Pour les scans, le score de reconnaissance correspond à celui de l’OCR. Sa calibration comme probabilité d’exactitude reste à mesurer. Une valeur absente ou deux valeurs différentes pour le même libellé provoquent une demande de confirmation. La revue humaine permet de tenir compte des erreurs de transcription avant la comparaison.

Le vérificateur calcule les verdicts à partir d’un profil et de contrôles documentaires. Le barème des fonds tient compte de la date de demande, du nombre de personnes, de la scolarité et du transport. Le Québec est renvoyé à une vérification spécifique. Une divergence sur les fonds empêche d’utiliser ce montant pour établir un verdict. Les contrôles documentaires distinguent présence déclarée, absence et information manquante. Les exigences sujettes à exception nécessitent la consultation d’IRCC. Une checklist associe à chaque contrôle une action et une source.

Le dossier porte sur des scénarios de demande standard depuis l’étranger. Les exceptions à la lettre d’acceptation, les exemptions PAL/TAL supplémentaires, les exceptions au CAQ et les consignes locales relèvent d’un examen humain. L’interface de démo enregistre une décision interne de transmission.

## Chapitre de mémoire — Interface, données et vérification

Le parcours distingue la préparation du dossier par le candidat de l’examen consultant. La confirmation des champs rend visible la responsabilité humaine. Les comptes de démo utilisent des données fictives. Les routes de consultation filtrent les dossiers par rôle et attribution. Les tests vérifient également le refus d’un téléchargement pour un tiers et la confidentialité des observations internes.

Le module `smart_immigration.dossier.agents` expose `read_document(task_id, content, kind, media_type)` et `check_dossier(task_id, dossier)`. Le premier renvoie les champs et un statut `needs_human`. Le second renvoie l’évaluation, la checklist, les contradictions et le nombre de champs en attente. L’appelant conserve le même identifiant de tâche entre les appels et lui transmet un `DossierRequest` avec les champs confirmés après la pause humaine. Le format partagé `AgentResult` reste celui du dépôt.

## Expériences et limites

Depuis la racine, avec l’environnement du projet activé, définir `$env:PYTHONPATH='src'`, puis lancer `python eval/dossier/benchmark.py`. Les annotations et réponses attendues sont dans `data/synthetic/evaluation/`.

- Extraction TXT. **149/149 champs conformes**, dont **142 valeurs attendues extraites** et 7 champs vides ou ambigus correctement laissés à confirmer.
- OCR. **12/12 valeurs détectées**, **10/12 reproduites exactement** sur les trois PDF scannés nets. Les écarts concernent un accent et un tiret. Le corpus TXT mesure surtout la lecture des libellés, et les trois PDF donnent une première mesure de l’OCR.
- Verdicts. **330/330** sur **30 profils** fictifs, dont les limites du barème, ses changements de date et le Québec. La mesure vérifie le comportement attendu sur ce jeu fictif.
- Contradictions P2. **30/30 cas conformes**, avec **15 alertes attendues et détectées**. Sans comparaison des pièces P2, ces 15 alertes seraient absentes. L’expérience sur le Contrôleur P1 reste à effectuer avec l’orchestrateur intégré.
- Durée et coût. **4,074 s** sur une exécution locale de l’évaluation P2 et **0 appel payant** pour ce périmètre. Le temps et le coût de V4 nécessitent une exécution de tout le système.

## Questions pour la répétition du jury

1. Comment les sources officielles sont-elles sélectionnées ?
2. Quelle est la différence entre la recherche lexicale et la recherche sémantique ?
3. Comment les documents sont-ils découpés et indexés ?
4. Comment mesure-t-on si la recherche ramène la bonne page ?
5. Comment le Chercheur sait-il qu’une réponse est suffisamment étayée ?
6. Comment distingue-t-on une citation utile d’un simple lien thématique ?
7. À quel moment le système s’abstient-il ?
8. Comment gère-t-on deux sources contradictoires ou de dates différentes ?
9. Comment le Contrôleur vérifie-t-il qu’une citation soutient une affirmation ?
10. Que se passe-t-il lorsqu’un document contient une instruction destinée au modèle ?
11. Où intervient la validation humaine dans le workflow ?
12. Quel état faut-il conserver pour reprendre une analyse interrompue ?
13. Comment comparer équitablement les quatre versions sur les mêmes cas ?
14. Que révèle l’expérience où l’on retire le Contrôleur ?
15. Quelles limites empêchent d’étendre directement l’évaluation à tous les pays ?

La capture demo-p2.webm illustre le parcours vérifié dans Edge, avec une base et deux comptes fictifs.
