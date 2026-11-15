from fastapi.testclient import TestClient

from smart_immigration.accounts.identity import IdentityAgent
from smart_immigration.accounts.routes import get_identity_agent
from smart_immigration.api import app

from .conftest import AlwaysMatch, fake_detector_one, login, png, register, verified_candidate

STUDY = {"motive": "study", "destination": "CA", "profile": {"family_size": 1, "funds_available_cad": 30000}}


def test_register_login_me_logout(client):
    assert register(client, "a@example.com").status_code == 201
    assert register(client, "a@example.com").status_code == 409
    assert login(client, "a@example.com").status_code == 200
    me = client.get("/auth/me").json()
    assert me["role"] == "candidate" and me["identity_status"] == "pending_identity"
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401


def test_short_password_and_wrong_password(client):
    r = client.post("/auth/register", json={"email": "b@example.com", "password": "court", "full_name": "B", "cin": "AB123456"})
    assert r.status_code == 422
    register(client, "b@example.com")
    assert login(client, "b@example.com", "mauvais-mot-de-passe").status_code == 401


def test_lockout_after_five_failures(client):
    register(client, "c@example.com")
    for _ in range(5):
        login(client, "c@example.com", "mauvais-mot-de-passe")
    assert login(client, "c@example.com").status_code == 429


def test_consultant_needs_invitation(client):
    assert register(client, "k@example.com", "consultant").status_code == 403
    assert register(client, "k@example.com", "consultant", "invite-test").status_code == 201


def test_unverified_candidate_cannot_create_request(client):
    register(client, "d@example.com"); login(client, "d@example.com")
    assert client.post("/requests", json=STUDY).status_code == 403


def test_identity_blurry_photo_asks_resubmit(client):
    register(client, "e@example.com"); login(client, "e@example.com")
    r = client.post("/identity/submit", files={"profile_photo": ("p.png", png(sharp=False), "image/png"), "cin": ("c.png", png(), "image/png")}).json()
    assert r["identity_status"] == "resubmit_requested" and "floue" in r["reasons"][0]
    # il peut renvoyer
    r = client.post("/identity/submit", files={"profile_photo": ("p.png", png(), "image/png"), "cin": ("c.png", png(), "image/png")}).json()
    assert r["identity_status"] == "verified"


def test_identity_low_match_asks_resubmit(client):
    app.dependency_overrides[get_identity_agent] = lambda: IdentityAgent(fake_detector_one, AlwaysMatch(0.1))
    register(client, "f@example.com"); login(client, "f@example.com")
    r = client.post("/identity/submit", files={"profile_photo": ("p.png", png(), "image/png"), "cin": ("c.png", png(), "image/png")}).json()
    assert r["identity_status"] == "resubmit_requested"


def test_identity_rejects_non_image(client):
    register(client, "g@example.com"); login(client, "g@example.com")
    r = client.post("/identity/submit", files={"profile_photo": ("p.txt", b"x", "text/plain"), "cin": ("c.png", png(), "image/png")})
    assert r.status_code == 422


def test_real_detector_finds_no_face_in_noise(client):
    app.dependency_overrides.clear()  # vrai détecteur OpenCV
    register(client, "h@example.com"); login(client, "h@example.com")
    r = client.post("/identity/submit", files={"profile_photo": ("p.png", png(), "image/png"), "cin": ("c.png", png(), "image/png")})
    if r.status_code == 503:  # OpenCV sans modèle : jamais de validation silencieuse
        assert client.get("/auth/me").json()["identity_status"] == "pending_identity"
    else:
        assert r.json()["identity_status"] == "resubmit_requested"


def test_full_flow_candidate_request_consultant_decision(client):
    verified_candidate(client)
    created = client.post("/requests", json=STUDY)
    assert created.status_code == 201
    rid = created.json()["id"]
    assert created.json()["recommendation"]["coverage"] == "full"
    assert created.json()["status"] == "awaiting_review"
    # le candidat ne peut pas décider
    assert client.post(f"/consultant/requests/{rid}/decision", json={"decision": "approved", "reason": "ok ok"}).status_code == 403

    consultant = TestClient(app)
    register(consultant, "cons@example.com", "consultant", "invite-test"); login(consultant, "cons@example.com")
    assert [r["id"] for r in consultant.get("/consultant/requests").json()] == [rid]
    d = consultant.post(f"/consultant/requests/{rid}/decision", json={"decision": "needs_info", "reason": "Relevé bancaire manquant"})
    assert d.json()["status"] == "needs_info"
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


# ---------- CIN à l'inscription, passeport facultatif ----------
def reg_raw(c, **kw):
    body = {"email": "z@example.com", "password": "motdepasse-solide", "full_name": "Z", **kw}
    return c.post("/auth/register", json=body)


def test_cin_is_required_for_candidate(client):
    assert reg_raw(client).status_code == 422


def test_cin_format_is_checked(client):
    for bad in ["12345678", "ABCD123456", "AB12345", "AB123456789", "AB12$456", "A B"]:
        assert reg_raw(client, cin=bad).status_code == 422, bad
    for good in ["A123456", "AB123456", "ABC12345678"]:
        client.cookies.clear()
        assert reg_raw(client, email=f"{good}@example.com", cin=good).status_code == 201, good


def test_cin_is_normalized_and_masked(client):
    r = reg_raw(client, cin=" ab 123456 ")
    assert r.status_code == 201
    assert r.json()["cin_masked"] == "*****456"
    assert "AB123456" not in r.text


def test_same_cin_cannot_open_two_accounts(client):
    assert reg_raw(client, cin="AB123456").status_code == 201
    assert reg_raw(client, email="y@example.com", cin="ab123456").status_code == 409


def test_cin_is_stored_encrypted(client):
    from sqlalchemy import select
    from smart_immigration.accounts import db as dbm
    from smart_immigration.accounts.models import User
    reg_raw(client, cin="AB123456")
    with dbm._factory() as s:
        u = s.scalar(select(User))
        assert "AB123456" not in (u.cin_enc or "") and "AB123456" not in (u.cin_hash or "")


def test_consultant_needs_no_cin(client):
    assert reg_raw(client, role="consultant", invitation="invite-test").json()["cin_masked"] is None


def test_passport_is_optional_then_added_in_profile(client):
    register(client, "p@example.com"); login(client, "p@example.com")
    assert client.get("/auth/me").json()["has_passport"] is False
    assert client.patch("/auth/me", json={"passport": "x"}).status_code == 422
    r = client.patch("/auth/me", json={"passport": "zb 1234567", "full_name": "Nouveau Nom"})
    assert r.json()["has_passport"] is True and r.json()["full_name"] == "Nouveau Nom"
    assert "ZB1234567" not in r.text


def test_passport_can_be_added_with_a_request(client):
    verified_candidate(client)
    assert client.post("/requests", json={**STUDY, "passport": "bad!"}).status_code == 422
    assert client.post("/requests", json={**STUDY, "passport": "ZB1234567"}).status_code == 201
    assert client.get("/auth/me").json()["has_passport"] is True
