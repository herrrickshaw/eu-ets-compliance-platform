from datetime import date

import pytest

from app import models
from app.modules.ets_core import router as ets_router

TODAY = date(2030, 6, 1)


class FrozenDate(date):
    @classmethod
    def today(cls):
        return TODAY


@pytest.fixture(autouse=True)
def frozen_today(monkeypatch):
    monkeypatch.setattr(ets_router, "date", FrozenDate)


def setup_installation(make, org, *, balance=100.0, verified=80.0, surrendered=0.0, deadline=date(2031, 4, 30), year=2029, holding=True):
    inst = make.add(models.Installation(org_id=org.id, name="Plant", country="DE", sector="steel"))
    acct = None
    if holding:
        acct = make.add(
            models.AllowanceAccount(
                org_id=org.id,
                installation_id=inst.id,
                account_type=models.AccountType.OPERATOR_HOLDING,
                balance=balance,
            )
        )
    cs = make.add(
        models.ComplianceStatus(
            installation_id=inst.id,
            year=year,
            verified_emissions_t=verified,
            allowances_surrendered_t=surrendered,
            surrender_deadline=deadline,
        )
    )
    return inst, acct, cs


def surrender(client, headers, inst, amount, year=2029):
    return client.post(
        "/api/ets/surrender",
        json={"installation_id": inst.id, "year": year, "amount_t": amount},
        headers=headers,
    )


def test_surrender_full_obligation_marks_compliant_and_debits_account(client, make, db, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, acct, cs = setup_installation(make, oa, balance=100, verified=80)
    r = surrender(client, ha, inst, 80)
    assert r.status_code == 200
    assert r.json()["status"] == "compliant"
    assert r.json()["allowances_surrendered_t"] == 80
    db.expire_all()
    assert db.get(models.AllowanceAccount, acct.id).balance == 20
    txn = db.query(models.AllowanceTransaction).one()
    assert (txn.account_id, txn.amount, txn.compliance_year) == (acct.id, 80, 2029)
    assert txn.txn_type == models.AllowanceTxnType.SURRENDER


def test_surrender_over_obligation_still_compliant(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa, balance=100, verified=80)
    assert surrender(client, ha, inst, 90).json()["status"] == "compliant"


def test_surrender_shortfall_before_deadline_is_short(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa, balance=100, verified=80, deadline=date(2030, 6, 2))
    assert surrender(client, ha, inst, 50).json()["status"] == "short"


def test_deadline_today_is_still_short_not_penalized(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa, deadline=TODAY)
    assert surrender(client, ha, inst, 10).json()["status"] == "short"


def test_deadline_yesterday_is_penalized(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa, deadline=date(2030, 5, 31))
    assert surrender(client, ha, inst, 10).json()["status"] == "penalized"


def test_surrender_accumulates_across_calls(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa, balance=100, verified=80)
    assert surrender(client, ha, inst, 30).json()["status"] == "short"
    r = surrender(client, ha, inst, 50)
    assert r.json()["allowances_surrendered_t"] == 80
    assert r.json()["status"] == "compliant"


def test_surrender_exact_balance_allowed_one_more_rejected(client, make, db, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, acct, _ = setup_installation(make, oa, balance=50, verified=80)
    r = surrender(client, ha, inst, 50.5)
    assert r.status_code == 400
    assert r.json()["detail"] == "Insufficient EUA balance: has 50.0, needs 50.5"
    assert db.query(models.AllowanceTransaction).count() == 0
    assert surrender(client, ha, inst, 50).status_code == 200
    db.expire_all()
    assert db.get(models.AllowanceAccount, acct.id).balance == 0


def test_surrender_not_found_cases(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    inst, _, _ = setup_installation(make, oa)
    assert client.post(
        "/api/ets/surrender", json={"installation_id": 999, "year": 2029, "amount_t": 1}, headers=ha
    ).status_code == 404
    r = surrender(client, ha, inst, 1, year=1999)
    assert (r.status_code, r.json()["detail"]) == (404, "No compliance record for that installation/year")
    no_acct, _, _ = setup_installation(make, oa, holding=False)
    r = surrender(client, ha, no_acct, 1)
    assert (r.status_code, r.json()["detail"]) == (404, "No operator holding account for this installation")


def test_surrender_other_tenants_installation_forbidden(client, make, db, two_tenants):
    (_, _, oa, _), (_, _, _, hb) = two_tenants
    inst, acct, cs = setup_installation(make, oa)
    r = surrender(client, hb, inst, 10)
    assert r.status_code == 403
    db.expire_all()
    assert db.get(models.AllowanceAccount, acct.id).balance == 100
    assert db.get(models.ComplianceStatus, cs.id).allowances_surrendered_t == 0


def test_listings_are_tenant_scoped_and_year_filtered(client, make, two_tenants):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    ia, _, _ = setup_installation(make, oa, year=2028)
    make.add(
        models.ComplianceStatus(
            installation_id=ia.id, year=2029, verified_emissions_t=1, surrender_deadline=date(2031, 1, 1)
        )
    )
    setup_installation(make, ob)

    inst = client.get("/api/ets/installations", headers=ha).json()
    assert [i["id"] for i in inst] == [ia.id]
    assert len(client.get("/api/ets/accounts", headers=ha).json()) == 1
    assert len(client.get("/api/ets/compliance", headers=ha).json()) == 2
    only_2029 = client.get("/api/ets/compliance?year=2029", headers=ha).json()
    assert [c["year"] for c in only_2029] == [2029]
    assert client.get("/api/ets/compliance?year=1999", headers=ha).json() == []
    # B sees only its own row
    assert len(client.get("/api/ets/compliance", headers=hb).json()) == 1


def test_system_stats_ordered_by_category_then_id(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    common = dict(period="p", unit="u", source_name="s", source_confidence=models.SourceConfidence.PRIMARY)
    for cat, label in [("b", "b1"), ("a", "a1"), ("a", "a2")]:
        make.add(models.EtsCoreSystemStat(category=cat, metric_label=label, **common))
    labels = [s["metric_label"] for s in client.get("/api/ets/system-stats", headers=ha).json()]
    assert labels == ["a1", "a2", "b1"]
