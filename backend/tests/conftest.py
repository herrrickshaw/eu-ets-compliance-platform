"""Shared fixtures: an in-memory SQLite DB per test (the real carbon_platform.db is never touched),
FastAPI dependency override for get_db, and helpers that create a tenant + org + bearer token."""
import os
import sys
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models  # noqa: E402
from app.auth.security import create_access_token  # noqa: E402
from app.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()

    def _get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    yield session
    session.close()
    app.dependency_overrides.clear()


@pytest.fixture
def client(db):
    # No `with` block: the startup hook (create_all on the real file DB) never runs.
    return TestClient(app)


@pytest.fixture
def tenant(db):
    """tenant('name', OrgType) -> (org, auth headers)."""
    counter = {"n": 0}

    def _make(name, org_type=models.OrgType.TRADER):
        counter["n"] += 1
        t = models.Tenant(name=name, slug=f"{name}-{counter['n']}")
        db.add(t)
        db.flush()
        u = models.User(tenant_id=t.id, email=f"{name}{counter['n']}@example.test", hashed_password="x")
        org = models.Organization(tenant_id=t.id, name=name, org_type=org_type)
        db.add_all([u, org])
        db.commit()
        return org, {"Authorization": f"Bearer {create_access_token(u.id, t.id)}"}

    return _make


@pytest.fixture
def eua(db):
    inst = models.Instrument(instrument_type=models.InstrumentType.EUA, symbol="EUA-TEST")
    db.add(inst)
    db.commit()
    return inst


def d(y, m, dd):
    return date(y, m, dd)
