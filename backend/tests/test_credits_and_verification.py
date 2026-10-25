"""Credit purchase/retire (credits/router.py) and stage->verify->commit (verification/router.py)."""
from datetime import date, datetime

import pytest

from app import models


def unit(db, status, owner=None):
    u = models.CreditUnit(issuance_id=1, quantity=100.0, status=status,
                          current_owner_org_id=owner.id if owner else None)
    db.add(u)
    db.commit()
    return u


def buy(client, h, u, org):
    return client.post(f"/api/credits/units/{u.id}/purchase", headers=h,
                       json={"unit_id": u.id, "buyer_org_id": org.id})


def test_issued_unit_can_be_bought_then_retired_by_owner_only(db, client, tenant):
    dev, _ = tenant("dev", models.OrgType.CREDIT_DEVELOPER)
    buyer, hb = tenant("buyer")
    _, hx = tenant("x")
    u = unit(db, models.CreditUnitStatus.ISSUED, dev)
    r = buy(client, hb, u, buyer).json()
    assert r["status"] == "held" and r["current_owner_org_id"] == buyer.id
    assert client.post(f"/api/credits/units/{u.id}/retire", headers=hx).status_code == 403
    assert client.post(f"/api/credits/units/{u.id}/retire", headers=hb).json()["status"] == "retired"
    assert buy(client, hb, u, buyer).status_code == 400  # retired


def test_staged_unit_not_purchasable(db, client, tenant):
    dev, _ = tenant("dev", models.OrgType.CREDIT_DEVELOPER)
    buyer, hb = tenant("buyer")
    assert buy(client, hb, unit(db, models.CreditUnitStatus.STAGED, dev), buyer).status_code == 400


def test_cannot_take_a_unit_another_tenant_already_holds(db, client, tenant):
    """HELD = owned. Letting any tenant 'purchase' it reassigns ownership with no seller consent."""
    owner, _ = tenant("owner")
    thief, ht = tenant("thief")
    u = unit(db, models.CreditUnitStatus.HELD, owner)
    r = buy(client, ht, u, thief)
    assert r.status_code == 400
    db.expire_all()
    assert db.get(models.CreditUnit, u.id).current_owner_org_id == owner.id


@pytest.fixture
def report(db, tenant):
    ship, hs = tenant("ship", models.OrgType.SHIPPING_COMPANY)
    v = models.Vessel(org_id=ship.id, imo_number="9", name="V", vessel_type="bulk", gross_tonnage=1.0)
    db.add(v)
    db.flush()
    rep = models.EmissionReport(vessel_id=v.id, year=2025, total_co2_t=1.0, ets_eligible_co2_t=1.0,
                                status=models.EmissionReportStatus.SUBMITTED)
    db.add(rep)
    db.commit()
    return ship, hs, rep


def decide(client, h, org, subject_type, subject_id, approve=True):
    return client.post("/api/verification/decide", headers=h,
                       json={"subject_type": subject_type, "subject_id": subject_id,
                             "verifier_org_id": org.id, "approve": approve})


def test_accredited_verifier_approval_issues_doc(db, client, tenant, report):
    _, hs, rep = report
    ver, hv = tenant("verifier", models.OrgType.VERIFIER)
    r = decide(client, hv, ver, "emission_report", rep.id)
    assert r.status_code == 200 and r.json()["status"] == "verified"
    db.expire_all()
    assert db.get(models.EmissionReport, rep.id).status == models.EmissionReportStatus.DOC_ISSUED
    # both the verifier and the subject's owner see the record; a third tenant does not
    assert len(client.get("/api/verification/records", headers=hv).json()) == 1
    assert len(client.get("/api/verification/records", headers=hs).json()) == 1
    _, hx = tenant("x")
    assert client.get("/api/verification/records", headers=hx).json() == []


def test_rejection_records_non_conformance_and_leaves_subject(db, client, tenant, report):
    _, _, rep = report
    ver, hv = tenant("verifier", models.OrgType.VERIFIER)
    assert decide(client, hv, ver, "emission_report", rep.id, approve=False).json()["status"] == "non_conformance"
    db.expire_all()
    assert db.get(models.EmissionReport, rep.id).status == models.EmissionReportStatus.SUBMITTED


def test_operator_cannot_verify_its_own_report(db, client, report):
    """The shipping company is not a verifier; self-approval must not issue a Document of Compliance."""
    ship, hs, rep = report
    r = decide(client, hs, ship, "emission_report", rep.id)
    assert r.status_code == 403
    db.expire_all()
    assert db.get(models.EmissionReport, rep.id).status == models.EmissionReportStatus.SUBMITTED


def test_verifier_approval_issues_staged_credit_unit(db, client, tenant):
    dev, _ = tenant("dev", models.OrgType.CREDIT_DEVELOPER)
    ver, hv = tenant("verifier", models.OrgType.VERIFIER)
    u = unit(db, models.CreditUnitStatus.STAGED, dev)
    decide(client, hv, ver, "credit_unit_batch", u.id)
    db.expire_all()
    assert db.get(models.CreditUnit, u.id).status == models.CreditUnitStatus.ISSUED
