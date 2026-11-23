"""Shared fixtures: every test runs against a private in-memory SQLite database.

The app's real engine points at a file on disk; tests never touch it. They
override the ``get_db`` dependency and build whatever rows they need through
the ``factory`` helpers below, so assertions are about the code's own logic on
synthetic data.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from app import db as appdb  # noqa: E402
from app import models  # noqa: E402
from app.auth.security import create_access_token, hash_password  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture
def engine():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    appdb.Base.metadata.create_all(bind=eng)
    yield eng
    eng.dispose()


@pytest.fixture
def Session(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)


@pytest.fixture
def db(Session):
    s = Session()
    yield s
    s.close()


@pytest.fixture
def client(Session):
    def _get_db():
        s = Session()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[appdb.get_db] = _get_db
    # no ``with`` -> the startup hook (which targets the on-disk DB) is not run
    yield TestClient(app)
    app.dependency_overrides.clear()


class Factory:
    def __init__(self, db):
        self.db = db
        self._n = 0

    def tenant(self, name="Acme", org_type=models.OrgType.ETS_OPERATOR, country="DE"):
        """One tenant + one user + one organization. Returns (tenant, user, org, headers)."""
        self._n += 1
        t = models.Tenant(name=name, slug=f"t{self._n}")
        self.db.add(t)
        self.db.flush()
        u = models.User(
            tenant_id=t.id,
            email=f"u{self._n}@example.test",
            hashed_password="x",
            role=models.UserRole.OWNER,
        )
        o = models.Organization(tenant_id=t.id, name=name, org_type=org_type, country=country)
        self.db.add_all([u, o])
        self.db.commit()
        headers = {"Authorization": f"Bearer {create_access_token(u.id, t.id)}"}
        return t, u, o, headers

    def add(self, *objs):
        self.db.add_all(objs)
        self.db.commit()
        for o in objs:
            self.db.refresh(o)
        return objs[0] if len(objs) == 1 else objs


@pytest.fixture
def make(db):
    return Factory(db)


@pytest.fixture
def two_tenants(make):
    """Tenant A and tenant B, each with one org."""
    return make.tenant("A"), make.tenant("B")
