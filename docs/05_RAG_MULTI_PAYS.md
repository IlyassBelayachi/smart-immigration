# RAG multi-pays (chaîne CONNAISSANCE)

## Ce qui est couvert
| Pays | Parcours | Sources officielles lues le 2026-11-20 |
|---|---|---|
| CA Canada | permis d'études | IRCC (4 pages vérifiées + pages à relire) |
| US États-Unis | visa étudiant F/M | travel.state.gov (2 pages), ICE frais SEVIS |
| SCHENGEN | visa de court séjour (90 jours) | Commission européenne (2 pages) |
| FR France | visa long séjour étudiant | France-Visas, Campus France |

**Limite importante** : la page européenne ne couvre que le court séjour. Les visas pour étudier ou travailler dans l'espace Schengen sont **nationaux** : chaque pays a ses règles. La France sert d'exemple ; ajouter un pays = ajouter un fichier `data/sources_<pays>.yaml`.
Les pages `studyinthestates.dhs.gov` et `uscis.gov` n'ont pas pu être lues (refusées) : elles ne sont pas dans le corpus.

## Comment ça marche
1. `data/sources*.yaml` : une liste de pages officielles par pays. `python -m smart_immigration.knowledge.ingest` (depuis `src/`, avec Internet) les télécharge et crée `data/corpus/chunks.jsonl`. Sans cela, le corpus d'amorçage `data/seed/seed_chunks.jsonl` (reformulations courtes avec URL, date) est utilisé.
2. `/ask` accepte `country` et `pathway` (optionnels) pour ne chercher que dans un pays. **Sans filtre, un passage d'un autre pays peut arriver en premier** : l'interface doit toujours envoyer le pays de la demande.
3. Recherche **hybride** (`RAG_EMBEDDINGS=1` + `pip install fastembed`) : mots-clés (BM25) + sens (embeddings multilingues), fusionnés par rangs (RRF). Sans cela, BM25 seul.
4. Le système ne répond que si le passage contient assez de mots de la question (sinon il s'abstient). Les vecteurs servent à classer, pas à autoriser une réponse.

## Évaluer
`python -m smart_immigration.knowledge.evaluate` (depuis `src/`) ; avec `RAG_EMBEDDINGS=1` il compare BM25 et hybride. Les 24 questions de `data/eval/questions.jsonl` ont été écrites par l'assistant à partir du corpus : les résultats sont **optimistes**. À faire : ajouter des questions écrites par vous deux, sans regarder le corpus, avant de citer un chiffre devant le jury.

## Pas encore fait
Seuils d'abstention non calibrés ; pas de LLM pour reformuler ; pas de règles de recommandation (checklist) pour US/Schengen/FR, seulement des réponses sourcées ; pages IRCC marquées `verified: false` à relire.
