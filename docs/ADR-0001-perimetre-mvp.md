# ADR-0001 — Périmètre du MVP

- **Date** : 2026-11-10
- **Statut** : proposée (à valider avec Mme Karboub)

## Contexte
Soutenance début janvier 2027 : environ 8 semaines de travail, dont 7 effectives avant le dépôt du mémoire.
Le cahier des charges v1.0 prévoyait Canada + France, deux parcours et une évaluation étendue (24 semaines).

## Décision
MVP limité au **Canada, permis d'études**. La France devient une perspective, démontrée par l'architecture configurable
(règles et sources déclaratives). Quatre agents (Research, Document, Règles/Checklist, Verification) orchestrés par un graphe LangGraph.
Évaluation : baselines B0–B3, ablation sur deux composants, trois hypothèses (H1 RAG hybride, H2 vérification, H4 coût du multi-agent).

## Conséquences
- (+) Profondeur et mesure plutôt que largeur ; règles vérifiables une à une sur les sources officielles.
- (−) Moins de couverture géographique ; à assumer explicitement dans le mémoire (section limites).

## Alternatives écartées
- Canada + France dès le MVP : double le travail de corpus, de règles et de benchmark pour un gain de démonstration limité.
- Corpus généraliste multi-pays : impossible à vérifier dans le temps imparti.
