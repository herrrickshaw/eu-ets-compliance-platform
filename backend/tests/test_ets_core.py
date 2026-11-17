"""EUA surrender in app/modules/ets_core/router.py."""
from datetime import date, timedelta

import pytest

from app import models


@pytest.fixture
def plant(db, tenant):
    org, h = tenant("op", models.OrgType.ETS_OPERATOR)
    inst = models.Installation(org_id=org.id, name="Kiln", country="DE", sector="cement")
    db.add(inst)
    db.flush()
    acct = models.AllowanceAccount(org_id=org.id, installation_id=inst.id,
                                   account_type=models.AccountType.OPERATOR_HOLDING, balance=1000.0)
    cs = models.ComplianceStatus(installation_id=inst.id, year=2025, verified_emissions_t=800.0,
                                 surrender_deadline=date.today() + timedelta(days=30))
    db.add_all([acct, cs])
    db.commit()
    return inst, acct, cs, h


def surrender(client, h, inst, amt, year=2025):
    return client.post("/api/ets/surrender", headers=h,
                       json={"installation_id": inst.id, "year": year, "amount_t": amt})


def test_partial_then_full_surrender(db, client, plant):
    inst, acct, cs, h = plant
    r = surrender(client, h, inst, 500)
    assert r.status_code == 200 and r.json()["status"] == "short"
    r = surrender(client, h, inst, 300).json()
    assert r["status"] == "compliant" and r["allowances_surrendered_t"] == 800
    db.expire_all()
    assert db.get(models.AllowanceAccount, acct.id).balance == 200
    assert db.query(models.AllowanceTransaction).count() == 2


def test_past_deadline_shortfall_is_penalized(db, client, plant):
    inst, acct, cs, h = plant
    cs.surrender_deadline = date.today() - timedelta(days=1)
    db.commit()
    assert surrender(client, h, inst, 100).json()["status"] == "penalized"


def test_insufficient_balance(client, plant):
    inst, _, _, h = plant
    assert surrender(client, h, inst, 1000.01).status_code == 400


def test_negative_surrender_cannot_mint_allowances(db, client, plant):
    """amount_t=-500 passes 'balance < amount' and then *adds* 500 EUAs to the account."""
    inst, acct, _, h = plant
    r = surrender(client, h, inst, -500)
    assert r.status_code == 422
    db.expire_all()
    assert db.get(models.AllowanceAccount, acct.id).balance == 1000


def test_other_tenant_cannot_surrender(client, tenant, plant):
    inst, *_ = plant
    _, other = tenant("intruder")
    assert surrender(client, other, inst, 10).status_code == 403


def test_installations_listing_is_tenant_scoped(client, tenant, plant):
    _, _, _, h = plant
    _, other = tenant("x")
    assert len(client.get("/api/ets/installations", headers=h).json()) == 1
    assert client.get("/api/ets/installations", headers=other).json() == []
