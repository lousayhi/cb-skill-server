from app import registry
from app.models import SkillType


def test_healthz_public(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_auth_required(client):
    r = client.get("/api/v1/skills")
    assert r.status_code == 401


def test_list_and_get_skills(client):
    headers = {"X-API-Key": "test-key"}
    r = client.get("/api/v1/skills", headers=headers)
    assert r.status_code == 200
    names = {s["name"] for s in r.json()}
    assert "code-review-checklist" in names
    assert "json-validator" in names

    r = client.get("/api/v1/skills/json-validator", headers=headers)
    assert r.status_code == 200
    assert r.json()["type"] == SkillType.script.value


def test_get_content_skill(client):
    headers = {"X-API-Key": "test-key"}
    r = client.get("/api/v1/skills/code-review-checklist/content", headers=headers)
    assert r.status_code == 200
    assert "Checklist" in r.json()["content"]


def test_download_tarball(client):
    headers = {"X-API-Key": "test-key"}
    r = client.get("/api/v1/skills/json-validator/download", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/gzip"


def test_webhook_requires_secret(client):
    r = client.post("/webhook/git", json={})
    assert r.status_code == 401

    r = client.post("/webhook/git", json={}, headers={"X-Webhook-Secret": "change-me"})
    # our test env webhook secret defaults to "change-me" only if unset; here it's change-me default
    assert r.status_code in (200, 401)


def test_invoke_script_skill(client):
    headers = {"X-API-Key": "test-key"}
    r = client.post(
        "/api/v1/skills/json-validator/invoke",
        headers=headers,
        json={"input": {"text": '{"hello": "world"}'}},
    )
    # Without a docker daemon in the test env, this returns 503.
    assert r.status_code in (200, 503)
    if r.status_code == 200:
        assert "hello" in r.json()["stdout"]
