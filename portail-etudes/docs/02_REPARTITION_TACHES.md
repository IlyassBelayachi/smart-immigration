# 02 — Qui fait quoi, sans se marcher dessus

> **Principe en une phrase : chacun a ses propres dossiers, on ne touche jamais aux fichiers de l'autre, et les deux parties se parlent uniquement par des « accords » écrits (section 3).**
> Proposition de départ : **Personne 1 = Ilyass**, **Personne 2 = Drief**. Vous avez les mêmes qualités : échangez les noms si vous préférez, en modifiant seulement les deux lignes marquées ci-dessous et le fichier `.github/CODEOWNERS`.

---

## 1. Le partage en deux « chaînes »

| | **Personne 1 — chaîne CONNAISSANCE** | **Personne 2 — chaîne DOSSIER** |
|---|---|---|
| **Question à laquelle elle répond** | « Que disent les règles officielles ? » | « Que dit le dossier du candidat, et est-il conforme ? » |
| **Contenu** | Copier et organiser les pages officielles, recherche, réponses avec sources, assistant Chercheur, Contrôleur, chef d'orchestre | Lire les documents, extraire les informations, règles et critères, liste des pièces manquantes, détection de contradictions, site web, sécurité, installation |
| **Résultat final visible** | Le chat sourcé et le fil de coordination des assistants | Le dossier du candidat, les verdicts, la checklist et le site web |
| **Mesures dont elle est responsable** | Qualité de la recherche, exactitude des sources citées, résistance aux documents piégés | Qualité de lecture des documents, justesse des verdicts, temps et coût du système complet |

Le **chef d'orchestre** (Personne 1) appelle les fonctions de la Personne 2 **seulement** via les accords de la section 3. Le **site web** (Personne 2) appelle les fonctions de la Personne 1 de la même manière.

## 2. À qui appartient chaque dossier

| Dossier ou fichier | Propriétaire |
|---|---|
| `src/smart_immigration/knowledge/` (collecte, recherche, réponses, routes) | **Personne 1** |
| `tests/knowledge/` · `eval/knowledge/` | **Personne 1** |
| `data/sources.yaml` · `data/seed/` · `data/corpus/` | **Personne 1** |
| `src/smart_immigration/dossier/` (règles, documents, checklist, routes) | **Personne 2** |
| `tests/dossier/` · `eval/dossier/` | **Personne 2** |
| `rules/` (règles écrites dans des fichiers) · `data/synthetic/` (documents fictifs) | **Personne 2** |
| `frontend/` (site web) · `docker-compose.yml` | **Personne 2** |
| `src/smart_immigration/schemas.py` (formes d'informations partagées) | **Les deux** (validation des deux) |
| `src/smart_immigration/api.py` (assemblage, aucune logique) | **Les deux** (ne change que pour brancher une nouvelle route) |
| `docs/` · `README.md` · `CLAUDE.md` · `requirements.txt` · `.github/` · mémoire | **Les deux** |

`.github/CODEOWNERS` applique cette table : GitHub demande **automatiquement** l'avis du bon propriétaire. (À compléter avec vos noms d'utilisateur GitHub, tâche J-02.)

## 3. Les « accords » entre vos deux parties

Ce sont des promesses du type « si tu m'envoies ceci, je te renvoie cela ». Tant que chacun les respecte, personne n'a besoin de lire le code de l'autre.

| Qui fournit | Fonction | Qui s'en sert | Ce qu'elle reçoit → ce qu'elle renvoie | État |
|---|---|---|---|---|
| P1 | `search(...)` / `answer(...)` | P2 (site web), chef d'orchestre | une question → une réponse + sources, ou un refus | ✅ existe (version mots exacts) |
| P2 | `assess(profil)` | P1 (chef d'orchestre) | un profil → un verdict par critère | ✅ existe (3 règles) |
| P2 | `build_checklist(profil, rapport)` | P1, site web | profil + verdicts → liste des pièces à fournir ou compléter | ⬜ S2 (D-06) |
| P2 | `extract_fields(fichier, type)` | P1 (chef d'orchestre) | un document → des champs extraits avec confiance | ⬜ S3 (D-09) |
| P2 | `find_contradictions(champs)` | P1 (Contrôleur) | champs de plusieurs documents → liste des contradictions | ⬜ S4 (D-15) |
| Les deux | Forme `AgentResult` (réponse standard d'un assistant) | tous | déjà définie dans `schemas.py` | ✅ existe |

**Règle des accords :** on peut **ajouter** des informations à une forme existante (nouveau champ optionnel). On ne **renomme ni ne supprime** rien sans accord des deux, annoncé la veille.

## 4. Les 12 règles anti-conflit

1. **Un dossier = un propriétaire.** On ne modifie pas les fichiers de l'autre, **même pour une faute de frappe** : on l'écrit à l'autre (message ou « Issue » GitHub).
2. **Jamais de travail directement sur `main`.** On travaille sur une **branche** nommée `p1/sujet` ou `p2/sujet` (exemple : `p1/recherche-par-le-sens`).
3. **Chaque matin : récupérer la dernière version** (`git pull`) avant de commencer. Chaque soir : envoyer son travail sur sa branche.
4. **Une branche vit 2 jours au maximum.** Plus elle vit longtemps, plus le risque de conflit grandit.
5. **Petites modifications.** Une demande de fusion (PR) = une idée, idéalement moins de 300 lignes.
6. **L'autre relit dans les 24 heures.** On fusionne après son accord. Le propriétaire du dossier a le dernier mot sur son dossier.
7. **Les fichiers communs** (`schemas.py`, `requirements.txt`, `docs/`) : on prévient avant (« demain je modifie X »). Dans `requirements.txt`, chacun n'écrit que dans **sa section**.
8. **Mise à jour de la documentation :** quand la vision, le périmètre ou une règle de travail change, on met à jour `docs/` dans la même demande de fusion. Le suivi (`docs/03`) est mis à jour **chaque lundi soir**.
9. **Si Git affiche un « conflit » :** on s'arrête, on ne choisit pas au hasard, on appelle l'autre et on règle ensemble. **Jamais** de `--force`.
10. **Secrets** (clés d'accès à l'IA, mots de passe) : **jamais dans GitHub**. Fichier `.env` local, déjà ignoré par Git.
11. **Blocage :** plus de 2 heures bloqué → on le dit à l'autre. Plus de 2 jours sur une piste sans résultat → on passe à la solution simple prévue (voir roadmap).
12. **Utilisation d'une IA :** on lui donne `CLAUDE.md`, on lui demande de ne toucher que **nos** fichiers, et on **relit et comprend** tout ce qu'elle écrit avant de le fusionner. À la soutenance, chacun doit pouvoir expliquer tout le projet.

## 5. Rythme de travail commun

| Quand | Quoi | Durée |
|---|---|---|
| Chaque jour | Point rapide : « ce que j'ai fait, ce que je fais, ce qui me bloque » | 15 min |
| Chaque semaine (lundi soir) | Revue : on montre ce qui marche, on met à jour `docs/03`, on prépare la semaine | 45 min |
| Chaque semaine | Une séance de travail à deux sur le point le plus difficile | 1 à 2 h |
| Toutes les deux semaines | Point court avec Mme Karboub (mail ou rencontre) | 20 min |

## 6. Les tâches, semaine par semaine

Légende : **J** = commun, **C** = Personne 1 (Connaissance), **D** = Personne 2 (Dossier). Le relecteur est toujours l'autre personne. Les semaines vont du **mardi au lundi**.

### S1 — 10 → 16 novembre : mettre en place

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| J-01 | Écrire à Mme Karboub : périmètre (Canada, permis d'études), date exacte de dépôt du mémoire et de soutenance, grille d'évaluation | P1 | Réponse reçue, dates notées dans `docs/03` |
| J-02 | Mettre le squelette sur GitHub, protéger `main`, vérifier que les tests automatiques passent, compléter `CODEOWNERS` | P1 | Les deux ont accès, les tests passent sur GitHub |
| J-03 | Lire ensemble `docs/01`, `docs/02` et `schemas.py`, corriger ce qui est flou | Les deux | Aucune question sans réponse |
| J-04 | Plan détaillé du mémoire (chaque personne détaille ses chapitres, voir S7) | Les deux | Plan dans `docs/` |
| C-01 | Compléter la liste des sources à 30–50 pages ; ouvrir et lire chacune, la passer en « vérifiée » | P1 | ≥ 30 pages vérifiées dans `data/sources.yaml` |
| C-02 | Lancer la collecte des pages sur votre ordinateur et contrôler 20 morceaux au hasard (pas de menus parasites) | P1 | Fichier `data/corpus/chunks.jsonl` propre |
| C-03 | Corriger le programme de collecte selon ce que le contrôle montre | P1 | Contrôle répété sans défaut |
| C-04 | Obtenir l'accès au modèle de langage (clé), préparer un appel de test, noter le choix dans une fiche | P1 | Un appel de test réussi, clé hors GitHub |
| C-05 | Préparer le GPU pour la recherche « par le sens » (CUDA, un petit modèle de test) | P1 | Un calcul réussi sur la RTX 3050 |
| D-01 | Relire les 3 règles actuelles contre les pages officielles ; corriger au besoin | P2 | Chaque règle a lien et date de lecture |
| D-02 | Ajouter 5 à 8 règles vérifiées (certificat de police, examen médical, biométrie, preuve de retour, etc.) avec un test chacune | P2 | Règles + tests dans `rules/` |
| D-03 | Définir les formes `Checklist` et `Contradiction` (demande de fusion « accord ») | P2 | Fusionné après accord de P1 |
| D-04 | Choisir les 3 types de documents fictifs et lister les champs à lire dans chacun | P2 | Liste validée par P1 |
| D-05 | Préparer le GPU pour la lecture de documents (OCR) | P2 | Un scan de test lu |

### S2 — 17 → 23 novembre : premier bout en bout (Démo n°1)

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-06 | Ajouter la recherche « par le sens » et la combiner avec la recherche par mots exacts | P1 | Test automatique + comparaison sur 20 questions |
| C-07 | Rédiger 40 questions avec leur bonne réponse (passage attendu) | P1 | `eval/knowledge/questions.jsonl` |
| C-08 | Écrire le script qui mesure la qualité de la recherche | P1 | Il affiche un tableau de résultats |
| D-06 | Fournir `build_checklist` : liste des pièces à fournir/compléter, avec sources | P2 | Route `/checklist` + tests |
| D-07 | Premier document fictif « SPÉCIMEN » + tester deux outils de lecture (1 journée max) + fiche de décision | P2 | Un outil choisi et justifié |
| D-08 | Site web minimal : un écran « question » et un écran « profil et verdicts » | P2 | Fonctionne avec les routes existantes |
| J-05 | **Démo n°1** : du profil à la réponse sourcée et à la checklist, filmée | Les deux | Vidéo + liste de ce qui manque |

### S3 — 24 → 30 novembre : approfondir et mesurer

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-09 | 20 questions de plus (total 60), dont 10 « pièges » (hors sujet, sources contradictoires) | P1 | Fichier complété |
| C-10 | Comparer V2 (recherche simple) et V3 (recherche améliorée) sur les 60 questions | P1 | Tableau de résultats enregistré |
| C-11 | Décider où ranger les données de recherche (fichier ou base de données), noter dans une fiche | P1 | Fiche écrite |
| D-09 | Lecture des 3 types de documents avec niveau de confiance | P2 | `extract_fields` fonctionne |
| D-10 | Fabriquer 40 documents fictifs avec leurs bonnes réponses | P2 | `data/synthetic/` + annotations |
| D-11 | Mesurer la qualité de lecture (informations extraites vs réelles) | P2 | Tableau enregistré |
| D-12 | Fabriquer 30 profils fictifs avec le verdict attendu ; viser 10–15 règles au total | P2 | Fichier + tests |

### S4 — 1 → 7 décembre : les assistants coordonnés

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-12 | Chef d'orchestre : enchaîne les étapes, pause pour validation humaine, reprise | P1 | Un scénario complet pause puis reprise |
| C-13 | Chercheur : reformule sa recherche, juge si c'est suffisant, s'abstient sinon | P1 | Tests sur les 10 questions pièges |
| C-14 | Contrôleur : vérifie les sources citées et bloque en cas de doute | P1 | Tests sur cas fautifs |
| D-13 | Brancher le Lecteur de documents comme assistant (forme `AgentResult`) | P2 | Appelé par le chef d'orchestre |
| D-14 | Brancher le Vérificateur de critères comme assistant | P2 | Appelé par le chef d'orchestre |
| D-15 | Détecter les contradictions entre documents (30 cas) | P2 | Fonction `find_contradictions` + tests |

### S5 — 8 → 14 décembre : site complet, sécurité, stabilité. **Gel le 14 décembre.**

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| D-16 | Site web de démonstration : profil fictif, dépôt de documents « SPÉCIMEN », chat sourcé, checklist avec validation | P2 | Démo de bout en bout sans donnée personnelle réelle |
| D-17 | Sécurité de base de la démo : comptes de test et droits d'accès aux documents fictifs (pas de vérification réelle de CIN/photo) | P2 | Tests de droits d'accès ; aucune donnée d'identité réelle |
| D-18 | Installation en une commande pour les deux | P2 | Fonctionne sur les deux ordinateurs |
| D-19 | Corrections de la chaîne Dossier | P2 | Plus d'erreur connue bloquante |
| C-15 | Tests avec 30 documents piégés (consignes cachées) | P1 | Taux de résistance mesuré |
| C-16 | Journal de ce qui s'est passé (qui a fait quoi, quand, avec quelle source) | P1 | Visible dans l'application |
| C-17 | Corrections de la chaîne Connaissance | P1 | Plus d'erreur connue bloquante |
| J-07 | **Gel des fonctions** : à partir du 14 décembre, on ne rajoute plus rien, on améliore et on mesure | Les deux | Annoncé et respecté |

### S6 — 15 → 21 décembre : les expériences

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-18 | Mesurer V1, V2, V3 sur les mêmes questions | P1 | Tableaux enregistrés |
| C-19 | Retirer la recherche « par le sens » et mesurer la différence | P1 | Tableau |
| C-20 | Mesurer temps et coût de la partie recherche | P1 | Tableau |
| D-20 | Faire tourner V4 (système complet) sur les scénarios | P2 | Résultats enregistrés |
| D-21 | Mesurer justesse des verdicts et qualité de lecture | P2 | Tableaux |
| D-22 | Retirer le Contrôleur et mesurer la différence | P2 | Tableau |
| D-23 | Mesurer temps et coût du système complet | P2 | Tableau |
| J-08 | Analyse des erreurs et conclusions honnêtes (forces et limites) | Les deux | Section « Résultats » rédigée |

*Cette semaine, chacun **fait tourner la chaîne de l'autre** pour la tester : c'est la meilleure préparation à la soutenance.*

### S7 — 22 → 28 décembre : le mémoire

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-21 | Chapitres : contexte et état de l'art, sources et recherche, résultats de recherche, éthique et limites | P1 | Relu par P2 |
| C-22 | Diaporama de soutenance : parties de P1 | P1 | Relu par P2 |
| D-24 | Chapitres : documents et règles, interface et sécurité, résultats de lecture et de verdicts | P2 | Relu par P1 |
| D-25 | Vidéo de démonstration de secours | P2 | Fichier prêt |
| J-09 | Introduction, conclusion, résumé du mémoire | Les deux | Mémoire déposé (date à confirmer, J-01) |

### S8 — 29 décembre → 4 janvier : répétitions et marge

| ID | Tâche | Qui | C'est fini quand… |
|---|---|---|---|
| C-23 | Écrire 15 questions de jury sur la partie de l'autre et les poser | P1 | Réponses solides |
| D-26 | Écrire 15 questions de jury sur la partie de l'autre et les poser | P2 | Réponses solides |
| J-10 | Deux répétitions complètes (avec chronomètre) ; rattraper les retards | Les deux | Soutenance prête |

## 7. Si quelqu'un prend du retard

- On le dit **le jour même** au point quotidien (pas à la fin de la semaine).
- Si le retard dépasse 2 jours : on **coupe la tâche la moins importante** de la semaine (jamais les mesures ni le mémoire).
- Solutions simples déjà prévues : site web en Streamlit si React traîne ; Tesseract si PaddleOCR bloque ; moins de documents fictifs (30 au lieu de 40).
- La semaine 8 est une **marge de sécurité**, pas du temps libre.
