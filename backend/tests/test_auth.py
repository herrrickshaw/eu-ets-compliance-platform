"""Auth: register/login/me and bearer-token enforcement."""
import jwt

from app.auth import security


def test_register_login_me_roundtrip(client):
    r = client.post("/api/auth/register", json={"tenant_name": "Acme Steel!", "email": "a@example.test",
                                                "password": "pw-123456"})
    assert r.status_code == 200
    assert r.json()["tenant"]["slug"] == "acme-steel"
    r2 = client.post("/api/auth/register", json={"tenant_name": "Acme Steel", "email": "b@example.test",
                                                 "password": "pw"})
    assert r2.json()["tenant"]["slug"] == "acme-steel-2"
    assert client.post("/api/auth/register", json={"tenant_name": "z", "email": "a@example.test",
                                                   "password": "pw"}).status_code == 400
    tok = client.post("/api/auth/login", json={"email": "a@example.test", "password": "pw-123456"}).json()["access_token"]
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"}).json()
    assert me["user"]["email"] == "a@example.test"
    assert client.post("/api/auth/login", json={"email": "a@example.test", "password": "nope"}).status_code == 401


def test_protected_routes_require_valid_token(client):
    assert client.get("/api/ets/installations").status_code == 401
    bad = jwt.encode({"sub": "1", "tenant_id": 1}, "wrong-secret", algorithm="HS256")
    assert client.get("/api/ets/installations", headers={"Authorization": f"Bearer {bad}"}).status_code == 401
    assert client.get("/api/health").json() == {"status": "ok"}


def test_slugify():
    from app.auth.router import _slugify
    assert _slugify("  Ünïcode & Co. ") == "n-code-co"
    assert _slugify("!!!") == "tenant"


def test_tokens_roundtrip():
    assert security.decode_access_token(security.create_access_token(7, 3))["sub"] == "7"
