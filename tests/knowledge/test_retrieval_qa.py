import pytest

from smart_immigration.knowledge.qa import answer
from smart_immigration.knowledge.retrieval import LexicalIndex, load_chunks, tokenize


@pytest.fixture(scope="module")
def index():
    return LexicalIndex(load_chunks())


OFFICIAL = {
    "CA": "https://www.canada.ca/",
    "US": ("https://travel.state.gov/", "https://www.ice.gov/"),
    "SCHENGEN": "https://home-affairs.ec.europa.eu/",
    "FR": ("https://france-visas.gouv.fr/", "https://www.campusfrance.org/"),
}


def test_seed_corpus_has_provenance():
    chunks = load_chunks()
    assert {c.country for c in chunks} == set(OFFICIAL)
    for c in chunks:
        assert c.url.startswith(OFFICIAL[c.country])
        assert c.retrieved_at is not None and c.content_hash


def test_tokenize_strips_accents():
    assert tokenize("Étudiant à Québec") == ["etudiant", "a", "quebec"]


def test_answers_with_citation(index):
    r = answer(index, "Do I need a provincial attestation letter to apply for a study permit?")
    assert r.answered and r.evidence
    assert r.evidence[0].source_id == "ircc-sp-pal"
    assert r.evidence[0].url.startswith("https://www.canada.ca/")


def test_financial_amount_question(index):
    r = answer(index, "How much living expenses money for one person outside Quebec?")
    assert r.answered
    assert r.evidence[0].source_id == "ircc-sp-financial"


def test_quebec_caq_question(index):
    r = answer(index, "What do I need to study in Quebec instead of a PAL?")
    assert r.answered and "CAQ" in r.answer


def test_abstains_out_of_scope(index):
    r = answer(index, "What is the best pizza restaurant in Casablanca?")
    assert not r.answered and r.abstention_reason and not r.evidence


def test_abstains_on_unrelated_country(index):
    r = answer(index, "German blue card salary threshold for engineers")
    assert not r.answered


def test_seed_fills_sources_missing_from_ingested_corpus(tmp_path, monkeypatch):
    """Si l'ingestion n'a pas pu telecharger une source (403), ses passages d'amorcage restent disponibles."""
    from smart_immigration.knowledge import retrieval

    seed = load_chunks(retrieval.SEED_PATH)
    ca = [c for c in seed if c.country == "CA"]
    corpus = tmp_path / "chunks.jsonl"
    corpus.write_text("\n".join(c.model_dump_json() for c in ca), encoding="utf-8")
    monkeypatch.setattr(retrieval, "CORPUS_PATH", corpus)
    merged = retrieval.load_chunks()
    assert {c.country for c in merged} == {"CA", "US", "SCHENGEN", "FR"}
    assert len(merged) == len(seed)  # aucun doublon : les sources deja ingerees ne sont pas reprises
