from datetime import date, datetime

import pytest

from app import models
from app.modules.verification.router import _subject_org_id

T = models.VerificationSubjectType
S = models.VerificationStatus


def report(make, org, status=models.EmissionReportStatus.SUBMITTED):
    v = make.add(models.Vessel(org_id=org.id, imo_number=f"I{org.id}{status.value}", name="v", vessel_type="t", gross_tonnage=1))
    return make.add(models.EmissionReport(vessel_id=v.id, year=2026, total_co2_t=1, ets_eligible_co2_t=1, status=status))


def credit_unit(make, dev, status=models.CreditUnitStatus.STAGED, owner=None):
    prog = make.add(models.CreditProgram(name="P"))
    meth = make.add(models.CreditMethodology(program_id=prog.id, name="M", sector="s"))
    proj = make.add(models.CreditProject(program_id=prog.id, methodology_id=meth.id, developer_org_id=dev.id, name="n", country="BR"))
    iss = make.add(models.CreditIssuance(project_id=proj.id, vintage_year=2024, quantity=1, issuance_date=date(2024, 1, 1)))
    return make.add(models.CreditUnit(issuance_id=iss.id, quantity=1, status=status, current_owner_org_id=owner))


def decide(client, headers, subject_type, subject_id, verifier, approve, findings=None):
    return client.post(
        "/api/verification/decide",
        json=dict(subject_type=subject_type, subject_id=subject_id, verifier_org_id=verifier.id, approve=approve, findings=findings),
        headers=headers,
    )


@pytest.fixture
def world(make, two_tenants):
    """A = verifier tenant, B = the tenant whose data is being verified, C = bystander."""
    a, b = two_tenants
    c = make.tenant("C")
    return a, b, c


def test_approve_emission_report_issues_doc_of_compliance(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    rep = report(make, ob)
    r = decide(client, hv, "emission_report", rep.id, ov, True, "all good")
    assert r.status_code == 200
    assert (r.json()["status"], r.json()["findings"]) == ("verified", "all good")
    assert r.json()["resolved_at"] is not None
    db.expire_all()
    assert db.get(models.EmissionReport, rep.id).status == models.EmissionReportStatus.DOC_ISSUED


def test_reject_records_non_conformance_and_leaves_subject_alone(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    rep = report(make, ob)
    r = decide(client, hv, "emission_report", rep.id, ov, False, "bad data")
    assert r.json()["status"] == "non_conformance"
    db.expire_all()
    assert db.get(models.EmissionReport, rep.id).status == models.EmissionReportStatus.SUBMITTED


def test_approve_credit_batch_issues_only_staged_units(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    staged = credit_unit(make, ob)
    held = credit_unit(make, ob, status=models.CreditUnitStatus.HELD, owner=ob.id)
    decide(client, hv, "credit_unit_batch", staged.id, ov, True)
    decide(client, hv, "credit_unit_batch", held.id, ov, True)
    db.expire_all()
    assert db.get(models.CreditUnit, staged.id).status == models.CreditUnitStatus.ISSUED
    assert db.get(models.CreditUnit, held.id).status == models.CreditUnitStatus.HELD


def test_rejecting_credit_batch_keeps_it_staged(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    u = credit_unit(make, ob)
    decide(client, hv, "credit_unit_batch", u.id, ov, False)
    db.expire_all()
    assert db.get(models.CreditUnit, u.id).status == models.CreditUnitStatus.STAGED


def test_approve_other_subject_types_changes_no_state_and_missing_subject_ok(client, db, world):
    (_, _, ov, hv), _, _ = world
    assert decide(client, hv, "cbam_declaration", 1, ov, True).json()["status"] == "verified"
    assert decide(client, hv, "installation_compliance", 1, ov, True).json()["status"] == "verified"
    assert decide(client, hv, "emission_report", 999, ov, True).json()["status"] == "verified"
    assert decide(client, hv, "credit_unit_batch", 999, ov, True).json()["status"] == "verified"


def test_second_decision_updates_latest_record_instead_of_inserting(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    rep = report(make, ob)
    first = decide(client, hv, "emission_report", rep.id, ov, False, "no").json()
    second = decide(client, hv, "emission_report", rep.id, ov, True, "yes").json()
    assert second["id"] == first["id"]
    assert (second["status"], second["findings"]) == ("verified", "yes")
    assert db.query(models.VerificationRecord).count() == 1


def test_decide_requires_verifier_org_in_callers_tenant(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    rep = report(make, ob)
    assert decide(client, hv, "emission_report", rep.id, ob, True).status_code == 403
    assert decide(client, hv, "emission_report", rep.id, type("O", (), {"id": 999}), True).status_code == 403
    assert db.query(models.VerificationRecord).count() == 0


def test_list_records_visible_to_verifier_and_subject_owner_only(client, make, world):
    (_, _, ov, hv), (_, _, ob, hb), (_, _, oc, hc) = world
    rep = report(make, ob)
    decide(client, hv, "emission_report", rep.id, ov, True)
    assert len(client.get("/api/verification/records", headers=hv).json()) == 1   # the verifier
    assert len(client.get("/api/verification/records", headers=hb).json()) == 1   # owner of the subject
    assert client.get("/api/verification/records", headers=hc).json() == []       # bystander


def test_list_records_status_filter(client, make, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    r1, r2 = report(make, ob), report(make, ob, status=models.EmissionReportStatus.DRAFT)
    decide(client, hv, "emission_report", r1.id, ov, True)
    decide(client, hv, "emission_report", r2.id, ov, False)
    assert len(client.get("/api/verification/records", headers=hv).json()) == 2
    ok = client.get("/api/verification/records?status=verified", headers=hv).json()
    assert [x["subject_id"] for x in ok] == [r1.id]
    assert client.get("/api/verification/records?status=pending", headers=hv).json() == []


def test_subject_org_resolution_for_each_type(make, db, world):
    _, (_, _, ob, _), _ = world
    rep = report(make, ob)
    inst = make.add(models.Installation(org_id=ob.id, name="i", country="DE", sector="s"))
    unit = credit_unit(make, ob, owner=ob.id)
    unowned = credit_unit(make, ob)
    declarant = make.add(models.CbamDeclarant(org_id=ob.id, eori_number="E"))
    decl = make.add(models.CbamDeclaration(declarant_id=declarant.id, year=2026, quarter=1, total_embedded_emissions_t=1))
    assert _subject_org_id(db, T.EMISSION_REPORT.value, rep.id) == ob.id
    assert _subject_org_id(db, T.INSTALLATION_COMPLIANCE.value, inst.id) == ob.id
    assert _subject_org_id(db, T.CREDIT_UNIT_BATCH.value, unit.id) == ob.id
    assert _subject_org_id(db, T.CREDIT_UNIT_BATCH.value, unowned.id) is None
    assert _subject_org_id(db, T.CBAM_DECLARATION.value, decl.id) == ob.id
    for t in T:
        assert _subject_org_id(db, t.value, 99999) is None
    assert _subject_org_id(db, "nonsense", 1) is None


def test_integrity_stats_ordering(client, make, world):
    (_, _, _, hv), _, _ = world
    common = dict(period="p", unit="u", source_name="s", source_confidence=models.SourceConfidence.PRIMARY)
    make.add(models.VerificationIntegrityStat(category="b", metric_label="b1", **common))
    make.add(models.VerificationIntegrityStat(category="a", metric_label="a1", **common))
    assert [x["metric_label"] for x in client.get("/api/verification/integrity-stats", headers=hv).json()] == ["a1", "b1"]


def test_decide_updates_the_most_recent_of_several_records(client, make, db, world):
    (_, _, ov, hv), (_, _, ob, _), _ = world
    rep = report(make, ob)
    old = make.add(models.VerificationRecord(subject_type=T.EMISSION_REPORT, subject_id=rep.id, verifier_org_id=ov.id))
    new = make.add(models.VerificationRecord(subject_type=T.EMISSION_REPORT, subject_id=rep.id, verifier_org_id=ov.id))
    r = decide(client, hv, "emission_report", rep.id, ov, True, "latest")
    assert r.json()["id"] == new.id
    db.expire_all()
    assert db.get(models.VerificationRecord, old.id).status == S.PENDING
