from datetime import date

import pytest

from app import models

ES = models.EmissionSource


@pytest.fixture
def declarant(make, two_tenants):
    (_, _, oa, ha), _ = two_tenants
    return make.add(models.CbamDeclarant(org_id=oa.id, eori_number="E1"))


def dv(make, cn="7208", country="default", direct=2.0, indirect=0.5, markup=10.0, valid=date(2026, 1, 1), name="Steel"):
    return make.add(
        models.CbamDefaultValue(
            cn_code=cn, good_name=name, country=country, direct_emissions_factor=direct,
            indirect_emissions_factor=indirect, markup_pct=markup, valid_from=valid,
        )
    )


def post_import(client, headers, declarant, **kw):
    body = dict(declarant_id=declarant.id, cn_code="7208", country_of_origin="IN", quantity_t=100, import_date="2026-02-10")
    body.update(kw)
    return client.post("/api/cbam/imports", json=body, headers=headers)


def test_import_uses_default_value_with_markup_and_rounding(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    dv(make, direct=2.0, indirect=0.5, markup=10.0)
    r = post_import(client, ha, declarant, quantity_t=100)
    assert r.status_code == 200
    b = r.json()
    assert b["emission_source"] == "default_value"
    assert b["direct_emissions_t"] == pytest.approx(220.0)  # 100 * 2.0 * 1.10
    assert b["indirect_emissions_t"] == pytest.approx(55.0)  # 100 * 0.5 * 1.10
    assert b["good_name"] == "Steel"


def test_import_rounds_to_three_decimals(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    dv(make, direct=1.23456, indirect=0.0, markup=0.0)
    b = post_import(client, ha, declarant, quantity_t=1).json()
    assert b["direct_emissions_t"] == 1.235


def test_country_specific_value_beats_default_and_latest_valid_from_wins(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    dv(make, country="default", direct=9.0, indirect=0.0, markup=0.0)
    dv(make, country="IN", direct=1.0, indirect=0.0, markup=0.0, valid=date(2025, 1, 1))
    dv(make, country="IN", direct=3.0, indirect=0.0, markup=0.0, valid=date(2026, 1, 1))
    assert post_import(client, ha, declarant, quantity_t=1).json()["direct_emissions_t"] == 3.0
    # an origin with no specific row falls back to "default"
    assert post_import(client, ha, declarant, quantity_t=1, country_of_origin="CN").json()["direct_emissions_t"] == 9.0


def test_actual_verified_emissions_bypass_default_table(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    b = post_import(client, ha, declarant, actual_direct_emissions_t=12.5, actual_indirect_emissions_t=2.5).json()
    assert b["emission_source"] == "actual_verified"
    assert (b["direct_emissions_t"], b["indirect_emissions_t"]) == (12.5, 2.5)
    assert b["good_name"] == "7208"  # no default row to take a name from -> CN code


def test_actual_direct_zero_is_still_actual_and_indirect_defaults_to_zero(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    dv(make)
    b = post_import(client, ha, declarant, actual_direct_emissions_t=0.0).json()
    assert b["emission_source"] == "actual_verified"
    assert (b["direct_emissions_t"], b["indirect_emissions_t"]) == (0.0, 0.0)
    assert b["good_name"] == "Steel"


def test_import_without_any_default_value_404(client, two_tenants, declarant, db):
    (_, _, _, ha), _ = two_tenants
    r = post_import(client, ha, declarant)
    assert (r.status_code, r.json()["detail"]) == (404, "No CBAM default value found for CN code 7208")
    assert db.query(models.CbamGoodsImport).count() == 0


def test_import_for_other_tenants_declarant(client, make, two_tenants, declarant):
    _, (_, _, _, hb) = two_tenants
    assert post_import(client, hb, declarant, actual_direct_emissions_t=1).status_code == 403
    assert client.post(
        "/api/cbam/imports",
        json=dict(declarant_id=999, cn_code="x", country_of_origin="IN", quantity_t=1, import_date="2026-01-01"),
        headers=hb,
    ).status_code == 404


def test_listings_scoped_to_tenant_with_declarant_filter(client, make, two_tenants, declarant):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    d2 = make.add(models.CbamDeclarant(org_id=oa.id, eori_number="E2"))
    other = make.add(models.CbamDeclarant(org_id=ob.id, eori_number="E3"))
    for d in (declarant, d2, other):
        make.add(models.CbamGoodsImport(declarant_id=d.id, cn_code="1", good_name="g", country_of_origin="IN",
                                        quantity_t=1, import_date=date(2026, 1, 1), direct_emissions_t=1))
        make.add(models.CbamDeclaration(declarant_id=d.id, year=2026, quarter=1, total_embedded_emissions_t=1))
    assert len(client.get("/api/cbam/declarants", headers=ha).json()) == 2
    assert len(client.get("/api/cbam/imports", headers=ha).json()) == 2
    only = client.get(f"/api/cbam/imports?declarant_id={d2.id}", headers=ha).json()
    assert [i["declarant_id"] for i in only] == [d2.id]
    assert len(client.get("/api/cbam/declarations", headers=ha).json()) == 2
    assert len(client.get(f"/api/cbam/declarations?declarant_id={declarant.id}", headers=ha).json()) == 1
    assert client.get(f"/api/cbam/imports?declarant_id={other.id}", headers=ha).json() == []
    assert len(client.get("/api/cbam/imports", headers=hb).json()) == 1


def test_default_values_filter(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    dv(make, cn="1111")
    dv(make, cn="2222")
    assert len(client.get("/api/cbam/default-values", headers=ha).json()) == 2
    assert [d["cn_code"] for d in client.get("/api/cbam/default-values?cn_code=2222", headers=ha).json()] == ["2222"]


def add_import(make, declarant, d, direct, indirect=0.0):
    make.add(models.CbamGoodsImport(declarant_id=declarant.id, cn_code="1", good_name="g", country_of_origin="IN",
                                    quantity_t=1, import_date=d, direct_emissions_t=direct, indirect_emissions_t=indirect))


def add_cert(make, declarant, qty, status=models.CbamCertificateStatus.HELD):
    return make.add(models.CbamCertificate(declarant_id=declarant.id, quantity_t_co2=qty, price_eur_per_t=1,
                                           purchase_date=date(2026, 1, 1), status=status))


def reconcile(client, headers, declarant, year, quarter):
    return client.post(f"/api/cbam/declarations/{declarant.id}/{year}/{quarter}/reconcile", headers=headers)


@pytest.mark.parametrize(
    "quarter,first,last,before,after",
    [
        (1, date(2026, 1, 1), date(2026, 3, 31), date(2025, 12, 31), date(2026, 4, 1)),
        (2, date(2026, 4, 1), date(2026, 6, 30), date(2026, 3, 31), date(2026, 7, 1)),
        (3, date(2026, 7, 1), date(2026, 9, 30), date(2026, 6, 30), date(2026, 10, 1)),
        (4, date(2026, 10, 1), date(2026, 12, 31), date(2026, 9, 30), date(2027, 1, 1)),
    ],
)
def test_reconcile_quarter_window_boundaries(client, make, two_tenants, declarant, quarter, first, last, before, after):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, first, 1.0, 0.5)
    add_import(make, declarant, last, 10.0)
    add_import(make, declarant, before, 100.0)
    add_import(make, declarant, after, 1000.0)
    r = reconcile(client, ha, declarant, 2026, quarter)
    assert r.status_code == 200
    assert r.json()["total_embedded_emissions_t"] == 11.5
    assert r.json()["status"] == "reconciled"
    assert (r.json()["year"], r.json()["quarter"]) == (2026, quarter)


def test_reconcile_nets_certificates_and_marks_fully_used_as_surrendered(client, make, db, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 10.0)
    c1 = add_cert(make, declarant, 6.0)
    c2 = add_cert(make, declarant, 6.0)
    r = reconcile(client, ha, declarant, 2026, 1)
    assert r.json()["certificates_surrendered_t"] == 10.0  # capped by liability
    db.expire_all()
    # c1 fully consumed (6), c2 only 4 of 6 -> stays HELD
    assert db.get(models.CbamCertificate, c1.id).status == models.CbamCertificateStatus.SURRENDERED
    assert db.get(models.CbamCertificate, c2.id).status == models.CbamCertificateStatus.HELD


def test_reconcile_surrender_capped_by_available_certificates(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 10.0)
    add_cert(make, declarant, 3.0)
    add_cert(make, declarant, 2.0, status=models.CbamCertificateStatus.REPURCHASED)  # not HELD -> ignored
    assert reconcile(client, ha, declarant, 2026, 1).json()["certificates_surrendered_t"] == 3.0


def test_reconcile_with_no_imports_creates_zero_declaration(client, db, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    r = reconcile(client, ha, declarant, 2026, 2)
    assert (r.json()["total_embedded_emissions_t"], r.json()["certificates_surrendered_t"]) == (0, 0)
    assert db.query(models.CbamDeclaration).count() == 1


def test_reconcile_updates_existing_declaration_instead_of_duplicating(client, make, db, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 4.0)
    first = reconcile(client, ha, declarant, 2026, 1).json()
    add_import(make, declarant, date(2026, 2, 15), 6.0)
    second = reconcile(client, ha, declarant, 2026, 1).json()
    assert second["id"] == first["id"]
    assert second["total_embedded_emissions_t"] == 10.0
    assert db.query(models.CbamDeclaration).count() == 1


def test_reconcile_rounds_total_to_three_decimals(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 0.12344, 0.00001)
    assert reconcile(client, ha, declarant, 2026, 1).json()["total_embedded_emissions_t"] == 0.123


def test_reconcile_tenant_check(client, two_tenants, declarant):
    _, (_, _, _, hb) = two_tenants
    assert reconcile(client, hb, declarant, 2026, 1).status_code == 403
    assert client.post("/api/cbam/declarations/9999/2026/1/reconcile", headers=hb).status_code == 404


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="reconcile_declaration only nets HELD certificates; a repeat reconcile of the same quarter "
    "finds none (the first run flipped them to SURRENDERED) and overwrites certificates_surrendered_t with 0",
)
def test_reconcile_is_idempotent_for_surrendered_total(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 10.0)
    add_cert(make, declarant, 10.0)
    first = reconcile(client, ha, declarant, 2026, 1).json()
    second = reconcile(client, ha, declarant, 2026, 1).json()
    assert first["certificates_surrendered_t"] == 10.0
    assert second["certificates_surrendered_t"] == first["certificates_surrendered_t"]


def add_schedule(make, rows):
    for y, pct in rows:
        make.add(models.CbamPhaseInSchedule(year=y, free_allocation_pct=100 - pct, cbam_factor_pct=pct))


def add_eua_price(make, price, d=date(2026, 1, 1)):
    inst = make.add(models.Instrument(instrument_type=models.InstrumentType.EUA, symbol="EUA"))
    make.add(models.PriceHistory(instrument_id=inst.id, price_date=date(2025, 1, 1), price_eur=price * 10))
    make.add(models.PriceHistory(instrument_id=inst.id, price_date=d, price_eur=price))


def test_phase_in_schedule_sorted_by_year(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    add_schedule(make, [(2028, 50), (2026, 10), (2027, 25)])
    assert [s["year"] for s in client.get("/api/cbam/phase-in-schedule", headers=ha).json()] == [2026, 2027, 2028]


def test_demand_analysis_arithmetic(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_schedule(make, [(2026, 10), (2027, 25)])
    add_eua_price(make, 80.0)
    add_import(make, declarant, date(2026, 3, 1), 70.0, 30.0)
    add_import(make, declarant, date(2026, 12, 31), 100.0)
    add_import(make, declarant, date(2025, 12, 31), 5000.0)  # other year, excluded
    add_import(make, declarant, date(2027, 1, 1), 5000.0)  # other year, excluded
    b = client.get("/api/cbam/demand-analysis?year=2026", headers=ha).json()
    assert b["declarant_count"] == 1
    assert b["total_embedded_emissions_t"] == 200.0
    assert b["cbam_factor_pct"] == 10.0
    assert b["actual_obligation_t"] == 20.0
    assert b["deferred_liability_t"] == 180.0
    assert b["reference_price_eur_per_t"] == 80.0  # latest date, not the earlier 800
    assert b["reference_price_date"] == "2026-01-01"
    assert b["actual_obligation_cost_eur"] == 1600.0
    assert b["full_liability_cost_eur"] == 16000.0
    assert b["methodology_note"]


def test_demand_analysis_schedule_fallbacks(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_schedule(make, [(2026, 10), (2030, 60)])
    add_import(make, declarant, date(2028, 5, 1), 100.0)
    # 2028 has no row -> first later year (2030)
    assert client.get("/api/cbam/demand-analysis?year=2028", headers=ha).json()["cbam_factor_pct"] == 60.0
    # beyond the last year -> the last row
    assert client.get("/api/cbam/demand-analysis?year=2040", headers=ha).json()["cbam_factor_pct"] == 60.0


def test_demand_analysis_without_schedule_price_or_declarants(client, two_tenants):
    (_, _, _, ha), _ = two_tenants
    b = client.get("/api/cbam/demand-analysis?year=2026", headers=ha).json()
    assert b["declarant_count"] == 0
    assert b["total_embedded_emissions_t"] == 0
    assert b["cbam_factor_pct"] == 100.0
    assert b["reference_price_eur_per_t"] is None
    assert b["actual_obligation_cost_eur"] is None and b["full_liability_cost_eur"] is None


def test_demand_analysis_is_tenant_scoped(client, make, two_tenants, declarant):
    _, (_, _, _, hb) = two_tenants
    add_import(make, declarant, date(2026, 3, 1), 50.0)
    assert client.get("/api/cbam/demand-analysis?year=2026", headers=hb).json()["total_embedded_emissions_t"] == 0


def test_demand_projection_across_schedule(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_schedule(make, [(2027, 25), (2026, 10)])
    add_eua_price(make, 50.0)
    add_import(make, declarant, date(2026, 6, 1), 150.0, 50.0)
    b = client.get("/api/cbam/demand-projection?base_year=2026", headers=ha).json()
    assert b["total_embedded_emissions_t"] == 200.0
    assert b["reference_price_eur_per_t"] == 50.0
    assert [(y["year"], y["cbam_factor_pct"], y["obligation_t"], y["obligation_cost_eur"]) for y in b["years"]] == [
        (2026, 10.0, 20.0, 1000.0),
        (2027, 25.0, 50.0, 2500.0),
    ]
    assert "2026" in b["note"]


def test_demand_projection_without_price(client, make, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_schedule(make, [(2026, 10)])
    b = client.get("/api/cbam/demand-projection?base_year=2026", headers=ha).json()
    assert b["reference_price_eur_per_t"] is None
    assert b["years"][0]["obligation_cost_eur"] is None


def test_reconcile_stops_consuming_once_liability_is_covered(client, make, db, two_tenants, declarant):
    (_, _, _, ha), _ = two_tenants
    add_import(make, declarant, date(2026, 1, 15), 5.0)
    c1 = add_cert(make, declarant, 6.0)
    c2 = add_cert(make, declarant, 6.0)
    assert reconcile(client, ha, declarant, 2026, 1).json()["certificates_surrendered_t"] == 5.0
    db.expire_all()
    assert db.get(models.CbamCertificate, c1.id).status == models.CbamCertificateStatus.HELD
    assert db.get(models.CbamCertificate, c2.id).status == models.CbamCertificateStatus.HELD
