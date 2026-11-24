import zlib

import numpy as np
from fastapi.testclient import TestClient

from smart_immigration.api import app
from smart_immigration.knowledge.evaluate import evaluate, load_questions
from smart_immigration.knowledge.qa import answer
from smart_immigration.knowledge.retrieval import LexicalIndex, allowed_mask, load_chunks
from smart_immigration.knowledge.vectors import HybridIndex, VectorIndex, chunk_text

client = TestClient(app)
SYNONYMS = {"canadian": "canada", "money": "financial", "funds": "financial"}


class FakeEmbedder:
    """Faux modele de sens : sacs de mots avec quelques synonymes. Compte les appels pour tester le cache."""

    def __init__(self):
        self.calls = 0

    def __call__(self, texts):
        self.calls += 1
        out = np.zeros((len(texts), 256), dtype=np.float32)
        for row, t in enumerate(texts):
            for w in t.lower().replace(".", " ").replace(",", " ").split():
                out[row, zlib.crc32(SYNONYMS.get(w, w).encode()) % 256] += 1
        return out


def hybrid(tmp_path=None, embed=None):
    lex = LexicalIndex(load_chunks())
    cache = tmp_path / "v.npy" if tmp_path else None
    return HybridIndex(lex, VectorIndex(lex.chunks, embed or FakeEmbedder(), cache))


def test_country_filter_only_returns_that_country():
    idx = LexicalIndex(load_chunks())
    for country in ("CA", "US", "SCHENGEN", "FR"):
        hits = idx.search("visa fee application documents", k=5, country=country)
        assert hits and {h.chunk.country for h in hits} == {country}


def test_filter_is_case_insensitive_and_pathway_works():
    chunks = load_chunks()
    assert allowed_mask(chunks, "us", None) == allowed_mask(chunks, "US", None)
    assert any(allowed_mask(chunks, None, "student_long_stay"))


def test_each_country_answers_with_its_own_source():
    idx = LexicalIndex(load_chunks())
    r = answer(idx, "How much is the SEVIS fee for an F-1 student?")
    assert r.answered and r.evidence[0].source_id == "us-ice-i901-faq" and r.evidence[0].country == "US"
    # sans filtre pays, un passage d'un autre pays peut passer devant : le filtre sert a ca
    r = answer(idx, "How long can I stay with a Schengen visa?", country="SCHENGEN")
    assert r.answered and r.evidence[0].source_id == "eu-apply-schengen-visa"
    r = answer(idx, "How long is the VLS-TS student visa valid?")
    assert r.answered and r.evidence[0].country == "FR"


def test_abstains_when_topic_not_in_chosen_country():
    idx = LexicalIndex(load_chunks())
    r = answer(idx, "How much is the SEVIS fee for an F-1 student?", country="CA")
    assert not r.answered and "CA" in r.abstention_reason


def test_eval_set_quality_floor():
    res = evaluate(LexicalIndex(load_chunks()), load_questions())
    hit, total = map(int, res["hit@3"].split("/"))
    assert hit / total >= 0.85
    assert res["abstentions correctes"] == "3/3"


def test_hybrid_answers_and_keeps_abstention():
    h = hybrid()
    r = answer(h, "How much is the SEVIS fee for an F-1 student?")
    assert r.answered and r.evidence[0].source_id == "us-ice-i901-faq"
    assert r.retrieval["method"] == "hybrid-rrf" and "top_cosine" in r.retrieval
    assert not answer(h, "What is the best pizza restaurant in Casablanca?").answered


def test_rrf_lets_the_meaning_match_into_the_results():
    """Un passage mal classe par les mots-cles mais premier par le sens doit entrer dans le top."""
    lex = LexicalIndex(load_chunks())
    target = next(i for i, c in enumerate(lex.chunks) if c.source_id == "ircc-sp-eligibility")

    class Stub:  # similarites imposees : la cible est la plus proche en sens
        def similarities(self, query):
            sims = np.zeros(len(lex.chunks))
            sims[target] = 1.0
            return sims

    query = "Who can apply for a Canadian study permit?"
    assert "ircc-sp-eligibility" not in [h.chunk.source_id for h in lex.search(query, k=3)]
    fused = HybridIndex(lex, Stub()).search(query, k=3)
    assert "ircc-sp-eligibility" in [h.chunk.source_id for h in fused]


def test_hybrid_respects_country_filter():
    h = hybrid()
    hits = h.search("visa fee", k=5, country="SCHENGEN")
    assert hits and {x.chunk.country for x in hits} == {"SCHENGEN"}


def test_vectors_are_cached(tmp_path):
    e = FakeEmbedder()
    hybrid(tmp_path, e)
    first = e.calls
    hybrid(tmp_path, e)  # meme corpus : lit le cache, n'embed pas les passages
    assert e.calls == first
    assert chunk_text(load_chunks()[0])


def test_api_filters_and_health():
    body = client.get("/health").json()
    assert set(body["countries"]) >= {"CA", "US", "SCHENGEN", "FR"} and body["method"] == "bm25"
    ok = client.post("/ask", json={"question": "How much is the SEVIS fee?", "country": "US"}).json()
    assert ok["answered"] and ok["evidence"][0]["country"] == "US"
    no = client.post("/ask", json={"question": "How much is the SEVIS fee?", "country": "FR"}).json()
    assert not no["answered"]
