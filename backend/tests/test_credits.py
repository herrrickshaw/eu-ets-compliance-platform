from datetime import date

import pytest

from app import models

U = models.CreditUnitStatus


def make_unit(make, dev_org, status=U.ISSUED, owner=None, country="BR", qty=10.0):
    prog = make.add(models.CreditProgram(name="Prog"))
    meth = make.add(models.CreditMethodology(program_id=prog.id, name="M", sector="forestry"))
    proj = make.add(
        models.CreditProject(
            program_id=prog.id, methodology_id=meth.id, developer_org_id=dev_org.id, name=f"P-{country}", country=country
        )
    )
    iss = make.add(models.CreditIssuance(project_id=proj.id, vintage_year=2024, quantity=qty, issuance_date=date(2024, 12, 31)))
    unit = make.add(models.CreditUnit(issuance_id=iss.id, quantity=qty, status=status, current_owner_org_id=owner))
    return proj, unit


def test_projects_visible_cross_tenant_and_country_filter(client, make, two_tenants):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    make_unit(make, ob, country="BR")
    make_unit(make, ob, country="KE")
    assert len(client.get("/api/credits/projects", headers=ha).json()) == 2
    ke = client.get("/api/credits/projects?country=KE", headers=ha).json()
    assert [p["country"] for p in ke] == ["KE"]
    assert client.get("/api/credits/projects?country=XX", headers=ha).json() == []


def test_units_status_filter(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    make_unit(make, oa, status=U.ISSUED)
    make_unit(make, oa, status=U.STAGED)
    assert len(client.get("/api/credits/units", headers=ha).json()) == 2
    staged = client.get("/api/credits/units?status=staged", headers=ha).json()
    assert [u["status"] for u in staged] == ["staged"]


def purchase(client, headers, unit_id, buyer_org_id):
    return client.post(
        f"/api/credits/units/{unit_id}/purchase",
        json={"unit_id": unit_id, "buyer_org_id": buyer_org_id},
        headers=headers,
    )


@pytest.mark.parametrize("status", [U.ISSUED, U.HELD])
def test_purchase_available_unit_moves_ownership_and_holds(client, make, db, two_tenants, status):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    _, unit = make_unit(make, ob, status=status)
    r = purchase(client, ha, unit.id, oa.id)
    assert r.status_code == 200
    assert r.json()["status"] == "held"
    assert r.json()["current_owner_org_id"] == oa.id


@pytest.mark.parametrize("status", [U.STAGED, U.RETIRED, U.TRANSFERRED])
def test_purchase_unavailable_unit_rejected(client, make, two_tenants, status):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    _, unit = make_unit(make, ob, status=status)
    r = purchase(client, ha, unit.id, oa.id)
    assert r.status_code == 400
    assert r.json()["detail"] == f"Unit is {status.value}, not available for purchase"


def test_purchase_buyer_must_be_in_callers_tenant(client, make, db, two_tenants):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    _, unit = make_unit(make, ob)
    assert purchase(client, ha, unit.id, ob.id).status_code == 403
    assert purchase(client, ha, unit.id, 9999).status_code == 403
    db.expire_all()
    assert db.get(models.CreditUnit, unit.id).current_owner_org_id is None


def test_purchase_missing_unit_404(client, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    assert purchase(client, ha, 404, oa.id).status_code == 404


def test_retire_held_unit_by_owner(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    _, unit = make_unit(make, oa, status=U.HELD, owner=oa.id)
    r = client.post(f"/api/credits/units/{unit.id}/retire", headers=ha)
    assert r.status_code == 200
    assert r.json()["status"] == "retired"


def test_retire_rejections(client, make, two_tenants):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    _, other = make_unit(make, ob, status=U.HELD, owner=ob.id)
    assert client.post(f"/api/credits/units/{other.id}/retire", headers=ha).status_code == 403
    _, unowned = make_unit(make, oa, status=U.HELD, owner=None)
    assert client.post(f"/api/credits/units/{unowned.id}/retire", headers=ha).status_code == 403
    _, issued = make_unit(make, oa, status=U.ISSUED, owner=oa.id)
    r = client.post(f"/api/credits/units/{issued.id}/retire", headers=ha)
    assert (r.status_code, r.json()["detail"]) == (400, "Only held units can be retired")
    assert client.post("/api/credits/units/9999/retire", headers=ha).status_code == 404


def test_global_market_stats_ordering(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    common = dict(period="p", unit="u", source_name="s", source_confidence=models.SourceConfidence.MODELED)
    for cat, label in [("z", "z1"), ("a", "a1")]:
        make.add(models.GlobalCarbonMarketStat(category=cat, metric_label=label, **common))
    labels = [s["metric_label"] for s in client.get("/api/credits/global-market-stats", headers=ha).json()]
    assert labels == ["a1", "z1"]
