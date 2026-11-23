from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app import models
from app.auth import security
from app.auth.router import _slugify
from app.db import DB_PATH, get_db


def test_password_hash_roundtrip():
    h = security.hash_password("s3cret")
    assert h != "s3cret"
    assert security.verify_password("s3cret", h) is True
    assert security.verify_password("S3cret", h) is False


def test_token_roundtrip_carries_subject_and_tenant():
    tok = security.create_access_token(7, 3)
    payload = security.decode_access_token(tok)
    assert payload["sub"] == "7"
    assert payload["tenant_id"] == 3


def test_token_expiry_is_twelve_hours():
    payload = security.decode_access_token(security.create_access_token(1, 1))
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    delta = exp - datetime.now(timezone.utc)
    assert timedelta(hours=11, minutes=59) < delta <= timedelta(hours=12)
    assert security.JWT_EXPIRE_MINUTES == 720


def test_token_signed_with_other_secret_rejected():
    bad = jwt.encode({"sub": "1"}, "other", algorithm="HS256")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_access_token(bad)


@pytest.mark.parametrize(
    "name,slug",
    [
        ("Nordic Steelworks AB", "nordic-steelworks-ab"),
        ("  --Hello,  World!!  ", "hello-world"),
        ("!!!", "tenant"),
        ("", "tenant"),
        ("ABC 123", "abc-123"),
    ],
)
def test_slugify(name, slug):
    assert _slugify(name) == slug


def register(client, tenant="Acme Corp", email="a@x.test", password="pw"):
    return client.post(
        "/api/auth/register", json={"tenant_name": tenant, "email": email, "password": password}
    )


def test_register_creates_tenant_owner_and_returns_working_token(client, db):
    r = register(client)
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["tenant"]["slug"] == "acme-corp"
    user = db.query(models.User).one()
    assert user.role == models.UserRole.OWNER
    assert user.hashed_password != "pw"
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["user"]["email"] == "a@x.test"
    assert me.json()["tenant"]["name"] == "Acme Corp"


def test_register_duplicate_email_rejected(client, db):
    assert register(client).status_code == 200
    r = register(client, tenant="Other")
    assert r.status_code == 400
    assert r.json()["detail"] == "Email already registered"
    assert db.query(models.Tenant).count() == 1


def test_register_same_tenant_name_gets_numbered_slugs(client, db):
    register(client, email="1@x.test")
    register(client, email="2@x.test")
    register(client, email="3@x.test")
    slugs = sorted(t.slug for t in db.query(models.Tenant).all())
    assert slugs == ["acme-corp", "acme-corp-2", "acme-corp-3"]


def test_login_success_and_failures(client):
    register(client)
    ok = client.post("/api/auth/login", json={"email": "a@x.test", "password": "pw"})
    assert ok.status_code == 200
    assert ok.json()["tenant"]["name"] == "Acme Corp"

    wrong_pw = client.post("/api/auth/login", json={"email": "a@x.test", "password": "nope"})
    assert wrong_pw.status_code == 401
    unknown = client.post("/api/auth/login", json={"email": "z@x.test", "password": "pw"})
    assert unknown.status_code == 401
    # same message for both: no account enumeration
    assert wrong_pw.json() == unknown.json() == {"detail": "Invalid email or password"}


def test_health_is_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}


PROTECTED = [
    "/api/orgs",
    "/api/auth/me",
    "/api/ets/installations",
    "/api/ets/accounts",
    "/api/ets/compliance",
    "/api/ets/system-stats",
    "/api/shipping/vessels",
    "/api/cbam/declarants",
    "/api/cbam/default-values",
    "/api/credits/projects",
    "/api/credits/units",
    "/api/verification/records",
    "/api/trading/instruments",
    "/api/trading/orders",
    "/api/india/sectors",
]


@pytest.mark.parametrize("url", PROTECTED)
def test_protected_endpoints_require_token(client, url):
    r = client.get(url)
    assert r.status_code == 401
    assert r.json()["detail"] == "Not authenticated"


def test_garbage_token_is_invalid(client):
    r = client.get("/api/orgs", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid token"


def test_expired_token_reported_as_expired(client, make):
    _, u, _, _ = make.tenant()
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    tok = jwt.encode(
        {"sub": str(u.id), "exp": past}, security.JWT_SECRET, algorithm=security.JWT_ALGORITHM
    )
    r = client.get("/api/orgs", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "Token expired"


def test_token_for_deleted_user_rejected(client):
    tok = security.create_access_token(9999, 1)
    r = client.get("/api/orgs", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401
    assert r.json()["detail"] == "User not found"


def test_orgs_directory_is_cross_tenant(client, two_tenants):
    (_, _, _, ha), (_, _, ob, _) = two_tenants
    names = {o["name"] for o in client.get("/api/orgs", headers=ha).json()}
    assert names == {"A", "B"}
    assert ob.name in names


def test_cors_allows_only_listed_dev_origins(client):
    good = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert good.headers.get("access-control-allow-origin") == "http://localhost:5173"
    bad = client.options(
        "/api/health",
        headers={"Origin": "http://evil.test", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers


def test_startup_hook_creates_tables(monkeypatch):
    from sqlalchemy import create_engine, inspect
    from sqlalchemy.pool import StaticPool

    from app import main

    eng = create_engine("sqlite://", poolclass=StaticPool)
    monkeypatch.setattr(main, "engine", eng)
    main.on_startup()
    assert {"users", "tenants", "orders"} <= set(inspect(eng).get_table_names())


def test_get_db_yields_session_and_closes():
    gen = get_db()
    s = next(gen)
    assert hasattr(s, "query")
    gen.close()
    assert DB_PATH.name == "carbon_platform.db"
    assert DB_PATH.parent.name == "backend"


def test_get_my_org_ids_scopes_to_tenant(db, two_tenants):
    from app.auth.deps import get_my_org_ids

    (ta, _, oa, _), (tb, _, ob, _) = two_tenants
    assert get_my_org_ids(db, ta.id) == [oa.id]
    assert get_my_org_ids(db, tb.id) == [ob.id]
    assert get_my_org_ids(db, 12345) == []
