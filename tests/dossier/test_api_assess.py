from fastapi.testclient import TestClient

from smart_immigration.api import app

client = TestClient(app)


def test_assess_endpoint_partial_profile():
    r = client.post("/assess", json={"has_letter_of_acceptance": True})
    assert r.status_code == 200
    verdicts = {x["rule_id"]: x["verdict"] for x in r.json()["results"]}
    assert verdicts["CA-SP-001"] == "MEETS"
    assert verdicts["CA-SP-003"] == "UNKNOWN"
    assert "juridique" in r.json()["disclaimer"]
