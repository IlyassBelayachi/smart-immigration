from base64 import b64encode
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from smart_immigration.api import app
from smart_immigration.dossier import portal


def _register(client, email, role, invitation=""):
    credentials = {"email": email, "password": "Fictif-Test-2026", "role": role}
    response = client.post("/portal/signup", json={**credentials, "name": email, "invitation": invitation})
    assert response.status_code == 201, response.text
    response = client.post("/portal/signin", json=credentials)
    assert response.status_code == 200
    return response.json()


def test_candidate_submission_and_consultant_review(tmp_path, monkeypatch):
    monkeypatch.setattr(portal, "DB_PATH", tmp_path / "portal.sqlite3")
    monkeypatch.setenv("IMMIGRATION_CONSULTANT_INVITE", "test-invitation")
    candidate, outsider, reviewer, successor = (TestClient(app) for _ in range(4))
    assert candidate.get("/portal/cases").status_code == 401
    assert reviewer.post("/portal/signup", json={
        "email": "reviewer@example.test", "password": "Fictif-Test-2026",
        "role": "consultant", "name": "Reviewer",
    }).status_code == 403
    _register(candidate, "candidate@example.test", "candidate")
    _register(outsider, "other@example.test", "candidate")
    _register(reviewer, "reviewer@example.test", "consultant", "test-invitation")
    next_consultant = _register(successor, "successor@example.test", "consultant", "test-invitation")

    content = candidate.get("/dossier/specimens/acceptance").content
    piece = candidate.post("/dossier/documents/acceptance", content=content,
                           headers={"Content-Type": "text/plain"}).json()
    dossier = {"profile": {}, "documents": [piece]}
    assert candidate.post("/portal/cases", json=dossier).status_code == 422
    for field in piece["fields"]:
        field["reviewed_by_human"] = True
    submitted = candidate.post("/portal/cases", json=dossier)
    assert submitted.status_code == 201
    assert outsider.get("/portal/cases").json()["cases"] == []
    assert candidate.post("/portal/cases", json=dossier).status_code == 409
    assert reviewer.post("/portal/cases", json=dossier).status_code == 403

    action = f"/portal/cases/{submitted.json()['id']}/actions"
    assert outsider.post(action, json={"action": "complete"}).status_code == 403
    result = reviewer.post(action, json={"action": "request_changes", "message": "Confirmer le programme."})
    assert result.json()["status"] == "needs_changes"
    assert successor.get("/portal/cases").json()["cases"] == []
    record = candidate.get("/portal/cases").json()["cases"][0]
    assert record["events"][-1]["message"] == "Confirmer le programme."
    assert candidate.post("/portal/cases", json=dossier).status_code == 201

    reassigned = reviewer.post(action, json={"action": "assign", "consultant_id": next_consultant["id"]})
    assert reassigned.status_code == 200
    assert reviewer.post(action, json={"action": "complete"}).status_code == 404
    assert successor.post(action, json={"action": "complete"}).json()["status"] == "completed"
    assert candidate.get("/portal/cases").json()["cases"][0]["status"] == "completed"
    assert candidate.post("/portal/signout").status_code == 204
    assert candidate.get("/portal/me").status_code == 401


def test_general_intake_persists_files_and_limits_download_access(tmp_path, monkeypatch):
    monkeypatch.setattr(portal, "DB_PATH", tmp_path / "portal.sqlite3")
    monkeypatch.setenv("IMMIGRATION_CONSULTANT_INVITE", "test-invitation")
    candidate, outsider, reviewer = (TestClient(app) for _ in range(3))
    credentials = {"email": "general@example.test", "password": "Fictif-Test-2026", "role": "candidate"}
    signup = candidate.post("/portal/signup", json={
        **credentials, "name": "Candidat fictif", "cin": "DEMO-CIN01", "passport": "DEMO-PASS01",
    })
    assert signup.status_code == 201
    assert candidate.post("/portal/signin", json=credentials).status_code == 200
    assert "cin" not in candidate.get("/portal/me").json()
    assert outsider.patch("/portal/me", json={"name": "Intrus"}).status_code == 401
    assert candidate.patch("/portal/me", json={"name": "Nouveau nom"}).status_code == 200
    assert candidate.get("/portal/me").json()["name"] == "Nouveau nom"
    _register(outsider, "other@example.test", "candidate")
    _register(reviewer, "reviewer@example.test", "consultant", "test-invitation")

    image = BytesIO()
    Image.new("RGB", (10, 10)).save(image, format="PNG")
    content = image.getvalue()
    file = {"kind": "photo", "filename": "portrait-specimen.png", "data": b64encode(content).decode()}
    body = {"destination": "FR", "purpose": "work", "description": "Projet fictif", "files": [file],
            "details": {"occupation": "Développeur", "residence": "Rabat, Maroc"}}
    draft = {key: value for key, value in body.items() if key != "files"}
    assert candidate.post("/portal/intake/draft", json=draft).status_code == 200
    assert candidate.get("/portal/intake/draft").json()["details"] == draft["details"]
    assert outsider.get("/portal/intake/draft").json() is None
    assert reviewer.get("/portal/intake/draft").status_code == 403
    assert outsider.post("/portal/intake", json={**body, "purpose": "study"}).status_code == 422
    assert outsider.post("/portal/intake", json={**body, "destination": "XX"}).status_code == 422
    assert outsider.post("/portal/intake", json={**body, "files": [{**file, "data": "YmFk"}]}).status_code == 422
    assert candidate.post("/portal/intake", json=body).status_code == 201
    assert candidate.get("/portal/intake/draft").json() is None
    assert candidate.post("/portal/intake/draft", json=draft).status_code == 409
    record = reviewer.get("/portal/cases").json()["cases"][0]
    assert "Développeur" in record["payload"]
    file_url = f"/portal/cases/{record['id']}/files/{record['files'][0]['id']}"
    assert outsider.get(file_url).status_code == 404
    assert candidate.get(file_url).content == content
    download = reviewer.get(file_url)
    assert download.content == content
    assert download.headers["content-disposition"].startswith("attachment;")
    action = f"/portal/cases/{record['id']}/actions"
    assert reviewer.post(action, json={"action": "note", "message": "Photo à vérifier."}).status_code == 200
    assert reviewer.get("/portal/cases").json()["cases"][0]["events"][-1]["action"] == "note"
    assert all(event["action"] != "note" for event in candidate.get("/portal/cases").json()["cases"][0]["events"])
    assert candidate.post(action, json={"action": "approve_transmission", "message": "Vérifié."}).status_code == 403
    assert reviewer.post(action, json={"action": "approve_transmission"}).status_code == 422
    approved = reviewer.post(action, json={"action": "approve_transmission", "message": "Pièces examinées."})
    assert approved.json()["status"] == "ready_to_send"
    candidate_record = candidate.get("/portal/cases").json()["cases"][0]
    assert candidate_record["events"][-1]["message"] == "Pièces examinées."
    assert reviewer.post(action, json={"action": "approve_transmission", "message": "Doublon."}).status_code == 409
