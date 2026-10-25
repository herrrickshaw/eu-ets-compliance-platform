"""THETIS-MRV style aggregation in app/modules/shipping_mrv/router.py."""
from datetime import datetime

import pytest

from app import models


@pytest.fixture
def ship(db, tenant):
    org, h = tenant("lines", models.OrgType.SHIPPING_COMPANY)
    v = models.Vessel(org_id=org.id, imo_number="9000001", name="Test", vessel_type="container", gross_tonnage=5e4)
    db.add(v)
    db.flush()

    def voy(t, fuel, intra):
        db.add(models.Voyage(vessel_id=v.id, departure_port="A", arrival_port="B", departure_time=t,
                             arrival_time=t, distance_nm=100, fuel_consumed_mt=fuel, intra_eu=intra))
    voy(datetime(2025, 1, 1, 0, 0), 100.0, True)
    voy(datetime(2025, 12, 31, 23, 0), 200.0, False)
    voy(datetime(2026, 1, 1, 0, 0), 999.0, True)  # next year, excluded
    db.commit()
    return v, h


def test_intra_eu_100pct_extra_eu_50pct(client, ship):
    v, h = ship
    r = client.post("/api/shipping/emission-reports/submit", headers=h, json={"vessel_id": v.id, "year": 2025})
    assert r.status_code == 200
    body = r.json()
    assert body["total_co2_t"] == pytest.approx(300 * 3.114, abs=0.01)
    assert body["ets_eligible_co2_t"] == pytest.approx((100 + 0.5 * 200) * 3.114, abs=0.01)
    assert body["status"] == "submitted"


def test_resubmit_updates_same_report(db, client, ship):
    v, h = ship
    for _ in range(2):
        client.post("/api/shipping/emission-reports/submit", headers=h, json={"vessel_id": v.id, "year": 2025})
    assert db.query(models.EmissionReport).count() == 1


def test_no_voyages_and_foreign_vessel(client, tenant, ship):
    v, h = ship
    assert client.post("/api/shipping/emission-reports/submit", headers=h,
                       json={"vessel_id": v.id, "year": 2019}).status_code == 404
    _, other = tenant("x")
    assert client.post("/api/shipping/emission-reports/submit", headers=other,
                       json={"vessel_id": v.id, "year": 2025}).status_code == 403
