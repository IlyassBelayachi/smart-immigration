from fastapi.testclient import TestClient

from smart_immigration.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["chunks"] > 0


def test_ask_endpoint():
    r = client.post("/ask", json={"question": "Is the biometrics fee required when I submit?"})
    assert r.status_code == 200
    body = r.json()
    assert body["answered"] and body["evidence"][0]["url"].startswith("https://")


def test_ask_validation():
    assert client.post("/ask", json={"question": "a"}).status_code == 422
