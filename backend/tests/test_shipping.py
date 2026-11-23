from datetime import datetime

import pytest

from app import models


def vessel(make, org, imo="IMO1"):
    return make.add(models.Vessel(org_id=org.id, imo_number=imo, name="MV Test", vessel_type="container", gross_tonnage=1000))


def voyage(make, v, depart, fuel, intra_eu):
    return make.add(
        models.Voyage(
            vessel_id=v.id, departure_port="A", arrival_port="B", departure_time=depart,
            arrival_time=depart, distance_nm=1, fuel_consumed_mt=fuel, intra_eu=intra_eu,
        )
    )


def submit(client, headers, v, year=2026):
    return client.post("/api/shipping/emission-reports/submit", json={"vessel_id": v.id, "year": year}, headers=headers)


def test_report_aggregates_fuel_to_co2_with_intra_extra_eu_weighting(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    v = vessel(make, oa)
    voyage(make, v, datetime(2026, 3, 1), 100.0, True)   # 100 % exposure
    voyage(make, v, datetime(2026, 4, 1), 200.0, False)  # 50 % exposure
    r = submit(client, ha, v)
    assert r.status_code == 200
    b = r.json()
    assert b["total_co2_t"] == pytest.approx(300 * 3.114, abs=0.01)
    assert b["ets_eligible_co2_t"] == pytest.approx((100 + 100) * 3.114, abs=0.01)
    assert b["status"] == "submitted"


def test_report_year_window_is_half_open(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    v = vessel(make, oa)
    voyage(make, v, datetime(2026, 1, 1, 0, 0, 0), 10.0, True)       # first instant of year: in
    voyage(make, v, datetime(2026, 12, 31, 23, 59, 59), 10.0, True)  # last second: in
    voyage(make, v, datetime(2025, 12, 31, 23, 59, 59), 1000.0, True)  # out
    voyage(make, v, datetime(2027, 1, 1, 0, 0, 0), 1000.0, True)       # out
    assert submit(client, ha, v).json()["total_co2_t"] == round(20 * 3.114, 2)


def test_report_rounds_to_two_decimals(client, make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    v = vessel(make, oa)
    voyage(make, v, datetime(2026, 5, 1), 1.0, True)
    assert submit(client, ha, v).json()["total_co2_t"] == 3.11


def test_resubmit_updates_the_same_report(client, make, db, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    v = vessel(make, oa)
    voyage(make, v, datetime(2026, 5, 1), 10.0, True)
    first = submit(client, ha, v).json()
    voyage(make, v, datetime(2026, 6, 1), 10.0, True)
    second = submit(client, ha, v).json()
    assert second["id"] == first["id"]
    assert second["total_co2_t"] == round(20 * 3.114, 2)
    assert db.query(models.EmissionReport).count() == 1


def test_resubmit_resets_verified_status_to_submitted(client, make, db, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    v = vessel(make, oa)
    voyage(make, v, datetime(2026, 5, 1), 10.0, True)
    make.add(models.EmissionReport(vessel_id=v.id, year=2026, total_co2_t=0, ets_eligible_co2_t=0,
                                   status=models.EmissionReportStatus.DOC_ISSUED))
    assert submit(client, ha, v).json()["status"] == "submitted"


def test_report_errors(client, make, two_tenants):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    v = vessel(make, oa)
    r = submit(client, ha, v)
    assert (r.status_code, r.json()["detail"]) == (404, "No voyages found for this vessel/year")
    assert client.post("/api/shipping/emission-reports/submit", json={"vessel_id": 99, "year": 2026}, headers=ha).status_code == 404
    voyage(make, v, datetime(2026, 5, 1), 10.0, True)
    assert submit(client, hb, v).status_code == 403


def test_listings_scoped_and_filtered_by_vessel(client, make, two_tenants):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    v1, v2, vb = vessel(make, oa, "I1"), vessel(make, oa, "I2"), vessel(make, ob, "I3")
    for v in (v1, v2, vb):
        voyage(make, v, datetime(2026, 1, 2), 1.0, True)
        make.add(models.MonitoringPlan(vessel_id=v.id))
        make.add(models.EmissionReport(vessel_id=v.id, year=2026, total_co2_t=1, ets_eligible_co2_t=1))
    assert len(client.get("/api/shipping/vessels", headers=ha).json()) == 2
    for path in ("monitoring-plans", "voyages", "emission-reports"):
        assert len(client.get(f"/api/shipping/{path}", headers=ha).json()) == 2
        one = client.get(f"/api/shipping/{path}?vessel_id={v2.id}", headers=ha).json()
        assert [x["vessel_id"] for x in one] == [v2.id]
        assert client.get(f"/api/shipping/{path}?vessel_id={vb.id}", headers=ha).json() == []
        assert len(client.get(f"/api/shipping/{path}", headers=hb).json()) == 1


def test_compliance_cost_ordering(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    common = dict(period="p", unit="u", source_name="s", source_confidence=models.SourceConfidence.MODELED)
    make.add(models.ShippingEtsComplianceCost(category="b", metric_label="b1", **common))
    make.add(models.ShippingEtsComplianceCost(category="a", metric_label="a1", **common))
    assert [x["metric_label"] for x in client.get("/api/shipping/ets-compliance-cost", headers=ha).json()] == ["a1", "b1"]
