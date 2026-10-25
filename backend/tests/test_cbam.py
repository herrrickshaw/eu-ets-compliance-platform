"""CBAM default-value fallback, quarterly reconciliation and phase-in maths (app/modules/cbam/router.py)."""
from datetime import date

import pytest

from app import models


@pytest.fixture
def decl(db, tenant):
    org, h = tenant("imp", models.OrgType.CBAM_DECLARANT)
    dc = models.CbamDeclarant(org_id=org.id, eori_number="DE123")
    db.add(dc)
    db.add_all([
        models.CbamDefaultValue(cn_code="7208", good_name="Flat steel", country="default",
                                direct_emissions_factor=2.0, indirect_emissions_factor=0.5, markup_pct=10,
                                valid_from=date(2026, 1, 1)),
        models.CbamDefaultValue(cn_code="7208", good_name="Flat steel", country="default",
                                direct_emissions_factor=1.0, indirect_emissions_factor=0.0, markup_pct=0,
                                valid_from=date(2024, 1, 1)),  # older, must not be used
        models.CbamDefaultValue(cn_code="7208", good_name="Flat steel", country="IN",
                                direct_emissions_factor=3.0, indirect_emissions_factor=1.0, markup_pct=20,
                                valid_from=date(2026, 1, 1)),
    ])
    db.commit()
    return dc, h


def imp(client, h, dc, **kw):
    body = {"declarant_id": dc.id, "cn_code": "7208", "country_of_origin": "CN", "quantity_t": 100,
            "import_date": "2026-02-10"}
    body.update(kw)
    return client.post("/api/cbam/imports", headers=h, json=body)


def test_default_value_uses_latest_rest_of_world_with_markup(client, decl):
    dc, h = decl
    r = imp(client, h, dc).json()
    assert r["emission_source"] == "default_value"
    assert r["direct_emissions_t"] == pytest.approx(100 * 2.0 * 1.10)
    assert r["indirect_emissions_t"] == pytest.approx(100 * 0.5 * 1.10)


def test_country_specific_default_preferred(client, decl):
    dc, h = decl
    r = imp(client, h, dc, country_of_origin="IN").json()
    assert r["direct_emissions_t"] == pytest.approx(360.0) and r["indirect_emissions_t"] == pytest.approx(120.0)


def test_actual_verified_emissions_override_defaults(client, decl):
    dc, h = decl
    r = imp(client, h, dc, actual_direct_emissions_t=42.0).json()
    assert r["emission_source"] == "actual_verified"
    assert r["direct_emissions_t"] == 42.0 and r["indirect_emissions_t"] == 0.0


def test_unknown_cn_code_is_404(client, decl):
    dc, h = decl
    assert imp(client, h, dc, cn_code="0000").status_code == 404


def reconcile(client, h, dc, y, q):
    return client.post(f"/api/cbam/declarations/{dc.id}/{y}/{q}/reconcile", headers=h)


def test_quarter_windows_including_q4_rollover(client, decl):
    dc, h = decl
    for dt in ("2025-12-31", "2026-01-01", "2026-03-31", "2026-04-01", "2026-12-31", "2027-01-01"):
        imp(client, h, dc, import_date=dt, actual_direct_emissions_t=1.0)
    assert reconcile(client, h, dc, 2026, 1).json()["total_embedded_emissions_t"] == 2.0
    assert reconcile(client, h, dc, 2026, 2).json()["total_embedded_emissions_t"] == 1.0
    assert reconcile(client, h, dc, 2026, 4).json()["total_embedded_emissions_t"] == 1.0
    assert reconcile(client, h, dc, 2025, 4).json()["total_embedded_emissions_t"] == 1.0


def test_partially_used_certificate_cannot_be_surrendered_twice(db, client, decl):
    """A 100 t certificate covering 60 t in Q1 has only 40 t left for Q2."""
    dc, h = decl
    db.add(models.CbamCertificate(declarant_id=dc.id, quantity_t_co2=100.0, price_eur_per_t=70.0,
                                  purchase_date=date(2026, 1, 1)))
    db.commit()
    imp(client, h, dc, import_date="2026-02-01", actual_direct_emissions_t=60.0)
    imp(client, h, dc, import_date="2026-05-01", actual_direct_emissions_t=60.0)
    q1 = reconcile(client, h, dc, 2026, 1).json()
    q2 = reconcile(client, h, dc, 2026, 2).json()
    assert q1["certificates_surrendered_t"] == 60.0
    assert q1["certificates_surrendered_t"] + q2["certificates_surrendered_t"] <= 100.0


def test_re_reconciling_same_quarter_does_not_consume_more_certificates(db, client, decl):
    dc, h = decl
    db.add_all([models.CbamCertificate(declarant_id=dc.id, quantity_t_co2=50.0, price_eur_per_t=70.0,
                                       purchase_date=date(2026, 1, 1)) for _ in range(2)])
    db.commit()
    imp(client, h, dc, import_date="2026-02-01", actual_direct_emissions_t=50.0)
    reconcile(client, h, dc, 2026, 1)
    again = reconcile(client, h, dc, 2026, 1).json()
    assert again["certificates_surrendered_t"] == 50.0
    held = db.query(models.CbamCertificate).filter_by(status=models.CbamCertificateStatus.HELD).count()
    assert held == 1


def test_demand_analysis_applies_phase_in_factor(db, client, decl, eua):
    dc, h = decl
    db.add(models.CbamPhaseInSchedule(year=2026, free_allocation_pct=97.5, cbam_factor_pct=2.5))
    db.add(models.PriceHistory(instrument_id=eua.id, price_date=date(2026, 1, 2), price_eur=80.0))
    db.commit()
    imp(client, h, dc, import_date="2026-02-01", actual_direct_emissions_t=1000.0)
    r = client.get("/api/cbam/demand-analysis?year=2026", headers=h).json()
    assert r["actual_obligation_t"] == 25.0 and r["deferred_liability_t"] == 975.0
    assert r["actual_obligation_cost_eur"] == 2000.0 and r["full_liability_cost_eur"] == 80000.0


def test_other_tenant_cannot_declare(client, tenant, decl):
    dc, _ = decl
    _, other = tenant("x")
    assert imp(client, other, dc).status_code == 403
