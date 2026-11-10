from datetime import date

from fastapi.testclient import TestClient

from smart_immigration.api import app

client = TestClient(app)


def test_demo_page_is_served():
    response = client.get("/demo/")

    assert response.status_code == 200
    assert "Smart Immigration" in response.text


def test_root_redirects_to_demo():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/demo/"


def test_demo_flow_returns_sourced_answer_verdicts_and_checklist():
    question = client.post(
        "/ask",
        json={"question": "Is the biometrics fee required when I submit?"},
    )
    profile = {"has_letter_of_acceptance": True}
    assessment = client.post("/assess", json=profile)
    checklist = client.post("/checklist", json=profile)

    assert question.status_code == assessment.status_code == checklist.status_code == 200
    assert question.json()["answered"] is True
    assert question.json()["evidence"][0]["url"].startswith("https://")
    assert len(assessment.json()["results"]) == 3
    acceptance = next(
        item for item in checklist.json()["items"] if item["rule_id"] == "CA-SP-001"
    )
    assert acceptance["status"] == "declared"


def test_checklist_returns_actions_and_official_sources():
    response = client.post(
        "/checklist",
        json={
            "destination_province": "ON",
            "level_of_study": "bachelor",
            "has_letter_of_acceptance": False,
            "pal_provided": False,
            "application_date": date(2026, 10, 1).isoformat(),
            "family_size": 1,
            "funds_available_cad": 1000,
            "tuition_first_year_cad": 15000,
            "transport_cost_cad": 2000,
        },
    )

    assert response.status_code == 200
    body = response.json()
    items = {item["rule_id"]: item for item in body["items"]}
    assert items["CA-SP-001"]["status"] == "to_provide"
    assert items["CA-SP-002"]["status"] == "to_provide"
    assert items["CA-SP-003"]["status"] == "to_provide"
    assert all(item["source_urls"][0].startswith("https://") for item in body["items"])


def test_checklist_marks_unknown_fields_for_confirmation():
    response = client.post("/checklist", json={})

    assert response.status_code == 200
    assert all(item["status"] == "to_confirm" for item in response.json()["items"])
    funds = next(item for item in response.json()["items"] if item["rule_id"] == "CA-SP-003")
    assert "application_date" in funds["missing_inputs"]


def test_checklist_does_not_claim_declared_documents_are_verified():
    response = client.post("/checklist", json={"has_letter_of_acceptance": True})

    assert response.status_code == 200
    acceptance = next(
        item for item in response.json()["items"] if item["rule_id"] == "CA-SP-001"
    )
    assert acceptance["status"] == "declared"
    assert "n'a pas ete verifie" in acceptance["message"]


def test_checklist_does_not_apply_federal_funds_threshold_to_quebec():
    response = client.post("/checklist", json={"destination_province": "QC"})

    assert response.status_code == 200
    funds = next(item for item in response.json()["items"] if item["rule_id"] == "CA-SP-003")
    assert funds["status"] == "not_assessed"
