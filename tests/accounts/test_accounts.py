import re

from fastapi.testclient import TestClient
from sqlalchemy import select

from smart_immigration.accounts import db as dbm
from smart_immigration.accounts import liveness, mailer
from smart_immigration.accounts.cin_ocr import cin_in_text
from smart_immigration.accounts.face import OpenCVFaceService
from smart_immigration.accounts.identity import IdentityAgent
from smart_immigration.accounts.models import IdentityDocument, User
from smart_immigration.accounts.routes import get_identity_agent
from smart_immigration.api import app

from .conftest import img, login, make_agent, register_consultant, signup, verified_candidate

STUDY = {"motive": "study", "destination": "CA", "profile": {"family_size": 1, "funds_available_cad": 30000}}


# ---------- Inscription = vérification d'identité ----------
def test_signup_creates_verified_account_and_login_works(client):
    r = signup(client, "a@example.com", cin="ab 123456")
    assert r.status_code == 201
    assert login(client, "a@example.com").status_code == 200
    me = client.get("/auth/me").json()
    assert me["role"] == "candidate" and me["identity_status"] == "verified" and me["cin_masked"] == "*****456"
    with dbm._factory() as s:
        kinds = sorted(d.kind for d in s.scalars(select(IdentityDocument)))
    assert kinds == ["cin", "profile_photo"]


def test_no_account_when_face_does_not_match_cin(client):
    r = signup(client, "b@example.com", person=1, cin_person=2)
    assert r.status_code == 422 and any("ne correspond pas" in x for x in r.json()["reasons"])
    assert login(client, "b@example.com").status_code == 401  # aucun compte créé
    assert signup(client, "b@example.com", cin="AB123456").status_code == 201  # on peut réessayer


def test_blurry_webcam_frame_is_refused_with_reason(client):
    r = signup(client, "c@example.com", problem_at=0)
    assert r.status_code == 422 and "floue" in " ".join(r.json()["reasons"])


def test_face_turned_away_is_refused(client):
    r = signup(client, "d@example.com", yaw_override=0.6)  # visage tourné : pas de face
    assert r.status_code == 422 and "de face" in " ".join(r.json()["reasons"])


def test_cin_file_cannot_be_used_as_live_photo(client):
    ch = client.get("/auth/signup/challenge").json()
    same = img(1, 0.0, seed=99)
    files = [("cin_image", ("c.png", same, "image/png")), ("frames", ("f.png", same, "image/png"))]
    data = {"email": "e@example.com", "password": "motdepasse-solide", "full_name": "E", "cin": "AB123456", "token": ch["token"]}
    r = client.post("/auth/signup", data=data, files=files)
    assert r.status_code == 422 and "utilisez la caméra" in " ".join(r.json()["reasons"])


def test_challenge_cannot_be_reused_or_forged(client):
    ch = client.get("/auth/signup/challenge").json()
    assert signup(client, "f@example.com", challenge=ch).status_code == 201
    assert signup(client, "g@example.com", challenge=ch).status_code == 422  # déjà servi
    assert signup(client, "h@example.com", challenge={**ch, "token": "faux.jeton.ici"}).status_code == 422


def test_too_many_failed_attempts_for_same_cin_are_blocked(client):
    for _ in range(5):
        assert signup(client, "i@example.com", cin="AB777777", person=1, cin_person=2).status_code == 422
    assert signup(client, "i@example.com", cin="AB777777").status_code == 429


def test_cin_ocr_rule(client):
    app.dependency_overrides[get_identity_agent] = lambda: make_agent(ocr=lambda b: ["ROYAUME DU MAROC", "AB 123456"])
    assert signup(client, "j@example.com", cin="AB123456").status_code == 201
    app.dependency_overrides[get_identity_agent] = lambda: make_agent(ocr=lambda b: ["ROYAUME DU MAROC", "XY 999999"])
    r = signup(client, "k@example.com", cin="CD654321")
    assert r.status_code == 422 and "numéro de CIN" in " ".join(r.json()["reasons"])
    app.dependency_overrides[get_identity_agent] = lambda: make_agent(ocr=lambda b: None)  # OCR absent : on continue
    assert signup(client, "l@example.com", cin="EF111111").status_code == 201


def test_ocr_matching_tolerates_common_confusions():
    assert cin_in_text("AB123456", ["AB 123456"])
    assert cin_in_text("AB123456", ["A8 1234S6"])
    assert not cin_in_text("AB123456", ["CD 654321"])


def test_liveness_helpers():
    assert liveness.make_steps() == ["center"]
    assert liveness.check_poses(["center"], [0.1]) == []
    assert len(liveness.check_poses(["center"], [0.6])) == 1 and len(liveness.check_poses(["center"], [-0.6])) == 1


def test_signup_validations_and_duplicates(client):
    assert signup(client, "m@example.com", cin="12345678").status_code == 422
    assert signup(client, "m@example.com", password="court").status_code == 422
    assert signup(client, "m@example.com", cin="AB123456").status_code == 201
    assert signup(client, "m@example.com", cin="CD123456").status_code == 409  # email déjà pris
    assert signup(client, "n@example.com", cin="ab123456").status_code == 409  # CIN déjà utilisée


def test_cin_is_stored_encrypted(client):
    signup(client, "o@example.com", cin="AB123456")
    with dbm._factory() as s:
        u = s.scalar(select(User))
        assert "AB123456" not in (u.cin_enc or "") and "AB123456" not in (u.cin_hash or "")


def test_candidates_cannot_register_without_identity_check(client):
    r = client.post("/auth/register", json={"email": "p@example.com", "password": "motdepasse-solide", "full_name": "P", "role": "candidate"})
    assert r.status_code == 403


# ---------- Connexion ----------
def test_login_me_logout_and_lockout(client):
    verified_candidate(client, "q@example.com")
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401
    for _ in range(5):
        login(client, "q@example.com", "mauvais-mot-de-passe")
    assert login(client, "q@example.com").status_code == 429


def test_consultant_needs_invitation_and_no_cin(client):
    assert register_consultant(client, invitation="mauvais").status_code == 403
    r = register_consultant(client)
    assert r.status_code == 201 and r.json()["cin_masked"] is None


# ---------- Email et mot de passe oublié ----------
def capture_mail(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send_mail", lambda to, subject, body: sent.append((to, subject, body)))
    return sent


def test_email_confirmation_flow(client, monkeypatch):
    monkeypatch.setenv("REQUIRE_EMAIL_CONFIRMATION", "1")
    sent = capture_mail(monkeypatch)
    r = signup(client, "r@example.com")
    assert r.status_code == 201 and r.json()["email_confirmation_required"] is True
    assert login(client, "r@example.com").status_code == 403  # email pas encore confirmé
    token = re.search(r"verify=([\w.\-]+)", sent[-1][2]).group(1)
    assert client.post("/auth/verify-email", json={"token": "faux"}).status_code == 400
    assert client.post("/auth/verify-email", json={"token": token}).status_code == 200
    assert login(client, "r@example.com").status_code == 200


def test_forgot_and_reset_password(client, monkeypatch):
    sent = capture_mail(monkeypatch)
    verified_candidate(client, "s@example.com")
    assert client.post("/auth/forgot-password", json={"email": "inconnu@example.com"}).status_code == 202
    assert sent == []  # même réponse, aucun email pour un compte inexistant
    assert client.post("/auth/forgot-password", json={"email": "s@example.com"}).status_code == 202
    token = re.search(r"reset=([\w.\-]+)", sent[-1][2]).group(1)
    assert client.post("/auth/reset-password", json={"token": token, "password": "nouveau-mot-de-passe"}).status_code == 200
    assert client.post("/auth/reset-password", json={"token": token, "password": "encore-un-autre-mdp"}).status_code == 400  # une seule fois
    assert login(client, "s@example.com", "motdepasse-solide").status_code == 401
    assert login(client, "s@example.com", "nouveau-mot-de-passe").status_code == 200


# ---------- Profil, passeport ----------
def test_passport_is_optional_then_added_in_profile_or_request(client):
    verified_candidate(client, "t@example.com")
    assert client.get("/auth/me").json()["has_passport"] is False
    assert client.patch("/auth/me", json={"passport": "bad!"}).status_code == 422
    assert client.patch("/auth/me", json={"passport": "ab1234567"}).json()["has_passport"] is True
    verified_candidate(client, "u@example.com")  # autre compte : le passeport vient avec la demande
    client.post("/requests", json={**STUDY, "passport": "zz9876543"})
    assert client.get("/auth/me").json()["has_passport"] is True


# ---------- Demandes et consultant ----------
def test_full_flow_candidate_request_consultant_decision(client):
    verified_candidate(client)
    created = client.post("/requests", json=STUDY)
    assert created.status_code == 201 and created.json()["recommendation"]["coverage"] == "full"
    rid = created.json()["id"]
    assert client.post(f"/consultant/requests/{rid}/decision", json={"decision": "approved", "reason": "ok ok"}).status_code == 403

    consultant = TestClient(app)
    register_consultant(consultant)
    login(consultant, "cons@example.com")
    assert [r["id"] for r in consultant.get("/consultant/requests").json()] == [rid]
    assert consultant.post(f"/consultant/requests/{rid}/decision", json={"decision": "needs_info", "reason": "Relevé manquant"}).json()["status"] == "needs_info"
    assert consultant.post(f"/consultant/requests/{rid}/decision", json={"decision": "approved", "reason": "Complet"}).json()["status"] == "approved"
    assert consultant.post(f"/consultant/requests/{rid}/decision", json={"decision": "rejected", "reason": "tard"}).status_code == 409
    mine = client.get("/requests").json()[0]
    assert mine["status"] == "approved" and len(mine["decisions"]) == 2


def test_uncovered_motive_is_flagged_for_human(client):
    verified_candidate(client)
    r = client.post("/requests", json={"motive": "family", "destination": "FR", "profile": {}}).json()
    assert r["recommendation"]["coverage"] == "not_covered"


def test_candidate_cannot_see_other_candidates_requests(client):
    verified_candidate(client, "one@example.com")
    client.post("/requests", json=STUDY)
    other = TestClient(app)
    verified_candidate(other, "two@example.com")
    assert other.get("/requests").json() == []


def test_consultant_endpoints_closed_to_candidates(client):
    verified_candidate(client)
    assert client.get("/consultant/requests").status_code == 403


def test_missing_face_models_give_503_and_no_account(client, tmp_path):
    app.dependency_overrides[get_identity_agent] = lambda: IdentityAgent(OpenCVFaceService(tmp_path), ocr=None)
    assert signup(client, "v@example.com").status_code == 503
    assert login(client, "v@example.com").status_code == 401
