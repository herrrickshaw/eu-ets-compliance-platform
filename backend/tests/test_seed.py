"""Run the demo seed script end to end against a private in-memory database."""
import pytest

from app import models
from app.seed import seed_data

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def seeded():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    eng = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    mp = pytest.MonkeyPatch()
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    mp.setattr(seed_data, "engine", eng)
    mp.setattr(seed_data, "SessionLocal", Session)
    seed_data.run()
    yield Session
    mp.undo()
    eng.dispose()


def test_seed_creates_one_user_per_org_with_demo_password(seeded):
    from app.auth.security import verify_password

    db = seeded()
    try:
        orgs = db.query(models.Organization).all()
        users = db.query(models.User).all()
        assert len(users) == len(orgs) >= 10
        assert {o.tenant_id for o in orgs} == {t.id for t in db.query(models.Tenant).all()}
        assert all(verify_password(seed_data.DEMO_PASSWORD, u.hashed_password) for u in users)
        assert all(u.email.startswith("demo@") and u.email.endswith(".example") for u in users)
    finally:
        db.close()


def test_seed_populates_every_domain_table(seeded):
    db = seeded()
    try:
        for model in (
            models.Installation, models.AllowanceAccount, models.ComplianceStatus, models.Vessel, models.Voyage,
            models.CbamDeclarant, models.CbamDefaultValue, models.CbamPhaseInSchedule, models.CreditProject,
            models.CreditUnit, models.Instrument, models.Order, models.PriceHistory, models.IndiaCctsSector,
            models.IndiaSupplyCapacity, models.CreditBenchmark, models.EtsCoreSystemStat,
        ):
            assert db.query(model).count() > 0, model.__name__
    finally:
        db.close()


def test_seed_is_idempotent_it_drops_and_recreates(seeded):
    db = seeded()
    try:
        before = db.query(models.Tenant).count()
    finally:
        db.close()
    seed_data.run()
    db = seeded()
    try:
        assert db.query(models.Tenant).count() == before
    finally:
        db.close()


def test_slugify_helper():
    assert seed_data._slugify("Nordic Steelworks AB") == "nordic-steelworks-ab"


@pytest.fixture
def seeded_client(seeded):
    from fastapi.testclient import TestClient

    from app import db as appdb
    from app.main import app

    def _get_db():
        s = seeded()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[appdb.get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(c, email):
    r = c.post("/api/auth/login", json={"email": email, "password": seed_data.DEMO_PASSWORD})
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


READ_ENDPOINTS = [
    "/api/orgs", "/api/auth/me",
    "/api/ets/installations", "/api/ets/accounts", "/api/ets/compliance", "/api/ets/system-stats",
    "/api/shipping/vessels", "/api/shipping/monitoring-plans", "/api/shipping/voyages",
    "/api/shipping/emission-reports", "/api/shipping/ets-compliance-cost",
    "/api/cbam/declarants", "/api/cbam/default-values", "/api/cbam/imports", "/api/cbam/declarations",
    "/api/cbam/phase-in-schedule", "/api/cbam/demand-analysis?year=2026", "/api/cbam/demand-projection?base_year=2026",
    "/api/credits/projects", "/api/credits/units", "/api/credits/global-market-stats",
    "/api/verification/records", "/api/verification/integrity-stats",
    "/api/trading/instruments", "/api/trading/orders", "/api/trading/trades", "/api/trading/positions",
    "/api/trading/market-reality",
    "/api/india/sectors", "/api/india/article6-activities", "/api/india/carbon-prices",
    "/api/india/supply-capacity", "/api/india/credit-benchmarks", "/api/india/cbam-export-exposure",
]


def test_every_read_endpoint_works_for_every_seeded_user(seeded_client, seeded):
    db = seeded()
    try:
        emails = [u.email for u in db.query(models.User).all()]
    finally:
        db.close()
    for email in emails:
        h = login(seeded_client, email)
        for url in READ_ENDPOINTS:
            r = seeded_client.get(url, headers=h)
            assert r.status_code == 200, (email, url, r.text[:200])


def test_seeded_post_endpoints(seeded_client):
    h = login(seeded_client, "demo@nordic-steelworks-ab.example")
    assert seeded_client.post("/api/india/demand-model", json={}, headers=h).status_code == 200
    gap = seeded_client.post("/api/india/gap-analysis", json={}, headers=h).json()
    assert gap["near_term_gap_mt_co2e"] == round(gap["total_demand_mt_co2e"] - gap["total_near_term_supply_mt_co2e"], 2)


def test_seeded_tenant_isolation_on_installations(seeded_client):
    steel = login(seeded_client, "demo@nordic-steelworks-ab.example")
    trader = login(seeded_client, "demo@meridian-carbon-trading-llp.example")
    names_steel = {i["name"] for i in seeded_client.get("/api/ets/installations", headers=steel).json()}
    assert names_steel
    assert seeded_client.get("/api/ets/installations", headers=trader).json() == []


def test_demo_password_matches_what_the_readme_and_login_page_advertise():
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    assert seed_data.DEMO_PASSWORD in (root / "README.md").read_text()
    assert seed_data.DEMO_PASSWORD in (root / "frontend" / "src" / "pages" / "Login.jsx").read_text()
