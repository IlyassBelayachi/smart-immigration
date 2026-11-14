import pytest
from fastapi.testclient import TestClient

from smart_immigration.accounts import db as dbm
from smart_immigration.accounts.identity import IdentityAgent
from smart_immigration.accounts.routes import get_identity_agent
from smart_immigration.api import app


class AlwaysMatch:
    name = "test-matcher"
    def __init__(self, score=0.9): self.score = score
    def similarity(self, a, b): return self.score


def fake_detector_one(img): return [(10, 10, 100, 100)]


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("CONSULTANT_INVITE", "invite-test")
    dbm.configure("sqlite:///:memory:")
    app.dependency_overrides[get_identity_agent] = lambda: IdentityAgent(fake_detector_one, AlwaysMatch())
    yield TestClient(app)
    app.dependency_overrides.clear()


def png(sharp=True, size=300):
    import cv2, numpy as np
    rng = np.random.default_rng(1)
    img = rng.integers(0, 255, (size, size, 3), dtype=np.uint8) if sharp else np.full((size, size, 3), 128, np.uint8)
    return cv2.imencode(".png", img)[1].tobytes()


def register(c, email, role="candidate", invitation=""):
    return c.post("/auth/register", json={"email": email, "password": "motdepasse-solide", "full_name": "Test", "role": role, "invitation": invitation})


def login(c, email, pw="motdepasse-solide"):
    return c.post("/auth/login", json={"email": email, "password": pw})


def verified_candidate(c, email="cand@example.com"):
    register(c, email); login(c, email)
    r = c.post("/identity/submit", files={"profile_photo": ("p.png", png(), "image/png"), "cin": ("c.png", png(), "image/png")})
    assert r.json()["identity_status"] == "verified", r.text
