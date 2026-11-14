from io import BytesIO
import unicodedata

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from smart_immigration.api import app

client = TestClient(app)


def _upload(document_type, content=None):
    if content is None:
        content = client.get(f"/dossier/specimens/{document_type}").content
    response = client.post(f"/dossier/documents/{document_type}", content=content,
                           headers={"Content-Type": "text/plain"})
    assert response.status_code == 200, response.text
    return response.json()


def _review(document):
    for field in document["fields"]:
        field["reviewed_by_human"] = True
    return document


def _report(documents, **profile):
    response = client.post("/dossier/report", json={"documents": documents, "profile": profile})
    assert response.status_code == 200, response.text
    return response.json()


def test_reviewed_financial_specimen_can_supply_funds():
    specimen = _upload("financial")
    profile = dict(destination_province="ON", application_date="2026-11-10", family_size=1,
                   tuition_first_year_cad=15000, transport_cost_cad=2000)
    pending = _report([specimen], **profile)
    assert pending["pending_fields"] == 4
    assert pending["funds_from_documents_cad"] is None
    assert not pending["can_validate"]

    reviewed = _report([_review(specimen)], **profile)
    assert reviewed["can_validate"]
    assert reviewed["funds_from_documents_cad"] == 45000
    funds = next(rule for rule in reviewed["assessment"]["results"] if rule["rule_id"] == "CA-SP-003")
    assert funds["verdict"] == "MEETS"


def test_contradictions_block_draft_until_resolved():
    acceptance = _review(_upload("acceptance"))
    transcript = _review(_upload("transcript"))
    financial = _review(_upload("financial"))
    name = next(field for field in transcript["fields"] if field["field_name"] == "candidate_name")
    name["value"] = "Maya Exemple"
    documents = [acceptance, transcript, financial]
    profile = dict(destination_province="ON", application_date="2026-11-10", family_size=1,
                   tuition_first_year_cad=15000, transport_cost_cad=2000)

    conflict = _report(documents, funds_available_cad=43000, **profile)
    assert not conflict["can_validate"]
    assert {item["field_name"] for item in conflict["contradictions"]} == {"candidate_name", "funds_available_cad"}
    funds = next(rule for rule in conflict["assessment"]["results"] if rule["rule_id"] == "CA-SP-003")
    assert funds["verdict"] == "UNKNOWN"
    assert funds["missing_inputs"] == ["funds_available_cad"]

    name["value"] = "Lina Exemple"
    resolved = _report(documents, funds_available_cad=45000, **profile)
    assert resolved["can_validate"]
    assert resolved["contradictions"] == []


def test_ambiguous_and_missing_fields_remain_pending():
    specimen = _review(_upload("acceptance", b"SPECIMEN\nNom: Lina Exemple\nNom: Maya Exemple\n"))
    assert specimen["fields"][0]["value"] is None
    assert _report([specimen])["pending_fields"] == 5


def test_rejects_non_specimen_and_oversized_files():
    path = "/dossier/documents/acceptance"
    headers = {"Content-Type": "text/plain"}
    assert client.post(path, content=b"Nom: Lina Exemple", headers=headers).status_code == 422
    assert client.post(path, content=b"x" * (2 * 1024 * 1024 + 1), headers=headers).status_code == 413
    assert client.post(path, content=b"SPECIMEN").status_code == 415


def test_reads_pdf_text_and_reports_page_number():
    pdf = PdfWriter()
    pdf.add_blank_page(width=300, height=300)
    page = pdf.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"),
                             NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 20 270 Td (SPECIMEN) Tj 0 -20 Td (Nom: Lina Exemple) Tj ET")
    page[NameObject("/Contents")] = stream
    buffer = BytesIO()
    pdf.write(buffer)
    response = client.post("/dossier/documents/acceptance", content=buffer.getvalue(),
                           headers={"Content-Type": "application/pdf"})
    assert response.status_code == 200, response.text
    name = response.json()["fields"][0]
    assert name["value"] == "Lina Exemple"
    assert name["page"] == 2


@pytest.mark.parametrize("document_type", ["acceptance", "transcript", "financial"])
def test_reads_all_fields_on_clean_raster_specimens(document_type):
    text = client.get(f"/dossier/specimens/{document_type}").content.decode("utf-8")
    expected = [line.split(":", 1)[1].strip() for line in text.splitlines() if ":" in line]
    content = client.get(f"/dossier/specimens/{document_type}?format=pdf").content
    assert not PdfReader(BytesIO(content)).pages[0].extract_text().strip()

    response = client.post(f"/dossier/documents/{document_type}", content=content,
                           headers={"Content-Type": "application/pdf"})
    assert response.status_code == 200, response.text
    fields = response.json()["fields"]
    def ignore_typography(value):
        decomposed = unicodedata.normalize("NFKD", value.replace("–", "-"))
        return "".join(letter for letter in decomposed if not unicodedata.combining(letter))

    assert all(field["value"] is not None for field in fields)
    assert [ignore_typography(field["value"]) for field in fields] == list(map(ignore_typography, expected))
    assert all(field["page"] == 1 and field["confidence"] is not None and not field["reviewed_by_human"]
               for field in fields)


@pytest.mark.parametrize("field,rule_id", [
    ("identity", "CA-SP-004"), ("medical", "CA-SP-005"), ("police", "CA-SP-006"),
    ("biometrics", "CA-SP-007"), ("local_documents", "CA-SP-008"),
])
def test_document_check_tracks_declared_status(field, rule_id):
    for status, expected in [(None, "to_confirm"), ("ready", "declared"), ("missing", "to_provide"),
                             ("not_required", "to_confirm" if field == "identity" else "declared")]:
        checks = {field: status} if status else {}
        response = client.post("/dossier/report", json={"profile": {}, "document_checks": checks})
        assert response.status_code == 200
        item = next(item for item in response.json()["checklist"]["items"] if item["rule_id"] == rule_id)
        assert item["status"] == expected
        assert item["source_urls"]


def test_accompanied_student_has_higher_funds_threshold():
    profile = dict(destination_province="ON", application_date="2026-11-11",
                   tuition_first_year_cad=15000, transport_cost_cad=2000, funds_available_cad=45000)
    for party, expected in [(1, "MEETS"), (2, "DOES_NOT_MEET")]:
        report = _report([], family_size=party, **profile)
        funds = next(item for item in report["assessment"]["results"] if item["rule_id"] == "CA-SP-003")
        assert funds["verdict"] == expected
