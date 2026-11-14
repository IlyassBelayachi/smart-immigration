import pytest

from smart_immigration.knowledge.qa import answer
from smart_immigration.knowledge.retrieval import LexicalIndex, load_chunks, tokenize


@pytest.fixture(scope="module")
def index():
    return LexicalIndex(load_chunks())


def test_seed_corpus_has_provenance():
    for c in load_chunks():
        assert c.url.startswith("https://www.canada.ca/")
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
