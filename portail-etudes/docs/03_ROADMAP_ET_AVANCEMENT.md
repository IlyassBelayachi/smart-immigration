# 03 — Feuille de route et suivi d'avancement

> **Ce document répond à deux questions : « Où va-t-on ? » et « Où en est-on ? ».**
> On le met à jour **chaque lundi soir** (règle 8 de `docs/02`). Dernière mise à jour : **mardi 10 novembre 2026**.

**Légende :** ✅ terminé · 🟡 en cours ou partiel · ⬜ pas commencé · 🔴 en retard

---

## 1. Avancement global : environ **14 %**

*C'est une estimation : chaque étape a un « poids » selon sa difficulté, et on compte la part réalisée.*

| # | Grande étape | Poids | Statut | Réalisé | Ce qui est fait / ce qui reste |
|---|---|---|---|---|---|
| E1 | Cadrage et plan validés | 5 | ✅ | 5 | Périmètre Canada / permis d'études décidé, plan en 8 semaines accepté |
| E2 | Dépôt GitHub et règles de travail | 5 | 🟡 | 3 | Dépôt créé, squelette livré, 3 documents de vision. Reste : tests vérifiés sur GitHub, `CODEOWNERS`, message à l'encadrante |
| E3 | Pages officielles copiées et vérifiées | 10 | 🟡 | 1 | 4 pages lues sur 30 à 50 visées. La collecte automatique n'est pas encore testée |
| E4 | Démo n°1 (question → réponse sourcée → verdicts → checklist) | 15 | 🟡 | 5 | Réponses sourcées par mots exacts et 3 règles fonctionnent. Reste : recherche « par le sens », checklist, site minimal |
| E5 | Lecture de documents (scans, PDF) | 10 | ⬜ | 0 | Tout reste à faire |
| E6 | Assistants coordonnés (chef d'orchestre, Chercheur, Contrôleur) | 15 | ⬜ | 0 | Tout reste à faire |
| E7 | Application complète (site web, comptes, installation) | 10 | ⬜ | 0 | Tout reste à faire |
| E8 | Tests, sécurité et **gel des fonctions (14 déc.)** | 5 | ⬜ | 0 | Tout reste à faire |
| E9 | Expériences et résultats (comparaison de 4 versions) | 10 | ⬜ | 0 | Le protocole est défini, aucune mesure faite |
| E10 | Mémoire, diaporama, soutenance | 15 | ⬜ | 0 | Plan à écrire en S1 |
| | **Total** | **100** | | **≈ 14** | |

## 2. La route en un coup d'œil

```
 S1          S2          S3          S4          S5          S6          S7          S8
10→16 nov  17→23 nov  24→30 nov  1→7 déc    8→14 déc   15→21 déc  22→28 déc  29 déc→4 jan
Mettre     DÉMO n°1   Approfondir Assistants  Site complet Expériences Mémoire    Répétitions
en place   (1er bout  et mesurer  coordonnés  + sécurité   (mesures)             et marge
           en bout)                           ⛔ GEL 14/12                          Soutenance
                                                                                    début janv.
```

| Date | Jalon | Ce que ça veut dire |
|---|---|---|
| **23 nov.** | Démo n°1 | Quelqu'un peut poser une question, voir la réponse avec sa source, et obtenir une liste de pièces à fournir |
| **30 nov.** | Premières mesures | On a des chiffres sur la recherche et la lecture de documents |
| **7 déc.** | Assistants coordonnés | Le système tourne de bout en bout, avec pause pour validation humaine |
| **14 déc.** | ⛔ **Gel des fonctions** | On n'ajoute plus rien. On améliore, on teste, on mesure |
| **21 déc.** | Résultats complets | Les 4 versions sont comparées |
| **28 déc.** | Mémoire déposé *(date à confirmer avec l'encadrante)* | Le texte est fini |
| **début janv.** | Soutenance *(date à confirmer)* | Prêts, après deux répétitions |

## 3. Cette semaine (S1 : 10 → 16 novembre)

| ID | Tâche | Qui | Statut |
|---|---|---|---|
| J-01 | Écrire à Mme Karboub (périmètre, dates, grille d'évaluation) | P1 | ⬜ |
| J-02 | Squelette sur GitHub, `main` protégé, tests verts, `CODEOWNERS` | P1 | 🟡 |
| J-03 | Lire ensemble les 3 documents et `schemas.py` | Les deux | ⬜ |
| J-04 | Plan détaillé du mémoire | Les deux | ⬜ |
| C-01 | Liste de 30–50 pages officielles lues et vérifiées | P1 | 🟡 (4/30) |
| C-02 | Collecte sur votre ordinateur + contrôle de 20 morceaux | P1 | ⬜ |
| C-03 | Corriger le programme de collecte | P1 | ⬜ |
| C-04 | Accès au modèle de langage + appel de test | P1 | ⬜ |
| C-05 | Préparer le GPU pour la recherche « par le sens » | P1 | ⬜ |
| D-01 | Relire les 3 règles contre les pages officielles | P2 | ⬜ |
| D-02 | Ajouter 5 à 8 règles vérifiées avec tests | P2 | ⬜ |
| D-03 | Définir les formes `Checklist` et `Contradiction` | P2 | ⬜ |
| D-04 | Choisir 3 types de documents fictifs et leurs champs | P2 | ⬜ |
| D-05 | Préparer le GPU pour la lecture de documents | P2 | ⬜ |

*(Le détail de toutes les semaines est dans `docs/02_REPARTITION_TACHES.md`, section 6.)*

## 4. Les 3 prochaines actions (les plus urgentes)

1. **Ce soir / demain :** Personne 1 envoie le message à Mme Karboub (J-01) et finalise GitHub (J-02).
2. **Demain :** les deux lisent `docs/01` et `docs/02`, puis un point à deux de 30 minutes pour se mettre d'accord (J-03).
3. **Cette semaine :** Personne 1 lit et valide les pages officielles (C-01) ; Personne 2 relit les règles (D-01).

## 5. Journal de bord hebdomadaire *(à remplir chaque lundi soir)*

| Semaine | Avancement global | Fait cette semaine | Retards ou blocages | Décisions prises |
|---|---|---|---|---|
| S0 (avant le 10 nov.) | 14 % | Plan resserré accepté, squelette livré, documents de vision | Aucun | Canada, permis d'études, 8 semaines |
| S1 | | | | |
| S2 | | | | |
| S3 | | | | |
| S4 | | | | |
| S5 | | | | |
| S6 | | | | |
| S7 | | | | |
| S8 | | | | |

## 6. Comment mettre à jour ce document (2 minutes)

1. Changer l'état des tâches de la semaine (⬜ → 🟡 → ✅).
2. Pour chaque grande étape (E1 à E10), estimer la part réalisée de son poids.
3. Additionner la colonne « Réalisé » : c'est l'avancement global.
4. Remplir la ligne de la semaine dans le journal de bord.
5. Si une date change, la corriger aussi dans la section 2.

## 7. Règles de réaction

| Situation | Réaction |
|---|---|
| L'avancement réel est en dessous de la route de plus d'une demi-semaine | On coupe la tâche la moins importante de la semaine (jamais les mesures ni le mémoire) |
| Une règle officielle change | On la corrige, on note la nouvelle date de lecture, on relance son test |
| L'encadrante change le périmètre | Mise à jour de `docs/01`, `docs/02` et de ce document dans la même demande de fusion |
