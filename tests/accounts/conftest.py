import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from smart_immigration.accounts import db as dbm
from smart_immigration.accounts.face import FaceObs, FaceProblem
from smart_immigration.accounts.identity import IdentityAgent
from smart_immigration.accounts.routes import get_identity_agent
from smart_immigration.api import app


def img(person=1, yaw=0.0, problem=0, seed=0):
    """Image de test : le pixel (0,0) code la personne, la pose et un éventuel problème."""
    rng = np.random.default_rng(seed)
    a = rng.integers(0, 255, (300, 300, 3), dtype=np.uint8)
    a[0, 0] = (problem, person, int(round(128 + yaw * 100)))
    return cv2.imencode(".png", a)[1].tobytes()


class FakeFaces:
    def analyze(self, data, kind):
        a = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if a is None:
            raise FaceProblem("fichier illisible.")
        problem, person, ycode = (int(v) for v in a[0, 0])
        if problem == 1:
            raise FaceProblem("image floue.")
        if problem == 2:
            raise FaceProblem("aucun visage détecté.")
        return FaceObs(embedding=person, yaw=(ycode - 128) / 100, sharpness=100.0)

    def similarity(self, a, b):
        return 0.9 if a.embedding == b.embedding else 0.1


def make_agent(ocr=None):
    return IdentityAgent(FakeFaces(), ocr=ocr)


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("CONSULTANT_INVITE", "invite-test")
    monkeypatch.setenv("DATA_ENCRYPTION_KEY", "cle-de-test")
    monkeypatch.setenv("REQUIRE_EMAIL_CONFIRMATION", "0")
    dbm.configure("sqlite:///:memory:")
    app.dependency_overrides[get_identity_agent] = lambda: make_agent()
    yield TestClient(app)
    app.dependency_overrides.clear()


POSE = {"center": 0.0}
_counter = {"n": 100000}


def next_cin():
    _counter["n"] += 1
    return f"AB{_counter['n']}"


def signup(c, email="cand@example.com", cin=None, password="motdepasse-solide", name="Test", person=1,
           cin_person=1, yaw_override=None, problem_at=None, challenge=None):
    ch = challenge or c.get("/auth/signup/challenge").json()
    steps = [s["key"] for s in ch["steps"]]
    frames = []
    for i, k in enumerate(steps):
        yaw = POSE[k] if yaw_override is None else yaw_override
        frames.append(("frames", (f"f{i}.png", img(person, yaw, 1 if problem_at == i else 0, seed=10 + i), "image/png")))
    files = [("cin_image", ("cin.png", img(cin_person, 0.0, seed=99), "image/png"))] + frames
    data = {"email": email, "password": password, "full_name": name, "cin": cin or next_cin(), "token": ch["token"]}
    return c.post("/auth/signup", data=data, files=files)


def login(c, email, pw="motdepasse-solide"):
    return c.post("/auth/login", json={"email": email, "password": pw})


def register_consultant(c, email="cons@example.com", invitation="invite-test"):
    return c.post("/auth/register", json={"email": email, "password": "motdepasse-solide", "full_name": "Consultant",
                                           "role": "consultant", "invitation": invitation})


def verified_candidate(c, email="cand@example.com", cin=None):
    r = signup(c, email, cin)
    assert r.status_code == 201, r.text
    assert login(c, email).status_code == 200
