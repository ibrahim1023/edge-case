from fastapi.testclient import TestClient

from edgecase.main import app

client = TestClient(app)


def test_session_lifecycle():
    r = client.post("/session")
    assert r.status_code == 200
    session = r.json()

    r = client.post(f"/session/{session['id']}/repository", json={"repository": "ibrahim1023/ci-rootcause"})
    assert r.status_code == 200

    r = client.post(f"/session/{session['id']}/confirm")
    assert r.status_code == 200

    r = client.get(f"/session/{session['id']}/findings")
    assert r.status_code == 200
    assert r.json() == []
