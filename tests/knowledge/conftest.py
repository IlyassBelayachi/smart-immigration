"""Les tests du RAG doivent donner le meme resultat partout : corpus d'amorcage, BM25 seul.

Ils ne doivent dependre ni du corpus telecharge sur votre machine (data/corpus/), ni de RAG_EMBEDDINGS.
"""
import os
from pathlib import Path

from smart_immigration.knowledge import retrieval

os.environ.pop("RAG_EMBEDDINGS", None)
retrieval.CORPUS_PATH = Path("__pas_de_corpus_telecharge__.jsonl")
