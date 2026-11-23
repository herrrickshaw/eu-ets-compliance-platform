from datetime import date

import pytest

from app import models

GS = models.GeiStatus
SC = models.SourceConfidence


def sector(make, key, vol, inten, pct, name=None, status=GS.FINAL):
    return make.add(
        models.IndiaCctsSector(
            key=key, name=name or key, status=status, target_reduction_pct_avg=pct,
            default_volume_mt=vol, default_intensity_tco2_per_t=inten, source_confidence=SC.PRIMARY,
        )
    )


def activity(make, name="act"):
    return make.add(models.Article6EligibleActivity(category=list(models.Article6Category)[0], name=name))


def supply(make, act, potential, ftype, label="m"):
    return make.add(
        models.IndiaSupplyCapacity(
            activity_id=act.id, metric_label=label, unit="MW", figure_type=ftype,
            source_name="src", source_confidence=SC.PRIMARY, potential_avoided_mt_co2e=potential,
        )
    )


def test_sectors_sorted_by_name(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    sector(make, "z", 1, 1, 1, name="Zinc")
    sector(make, "a", 1, 1, 1, name="Aluminium")
    assert [s["name"] for s in client.get("/api/india/sectors", headers=ha).json()] == ["Aluminium", "Zinc"]


def test_demand_model_default_arithmetic(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    sector(make, "a", 10, 2.5, 4.0, name="A")   # baseline 25, pool 1.0
    sector(make, "b", 3, 1.111, 7.0, name="B")  # baseline 3.333 -> 3.33, pool 0.23331 -> 0.23
    b = client.post("/api/india/demand-model", json={}, headers=ha).json()
    rows = {r["sector_key"]: r for r in b["sectors"]}
    assert rows["a"]["baseline_emissions_mt_co2e"] == 25.0
    assert rows["a"]["illustrative_abatement_pool_mt_co2e"] == 1.0
    assert rows["b"]["baseline_emissions_mt_co2e"] == 3.33
    assert rows["b"]["illustrative_abatement_pool_mt_co2e"] == 0.23
    assert b["total_illustrative_demand_mt_co2e"] == round(1.0 + 0.23331, 2)
    assert "Illustrative demand model" in b["methodology_note"]


def test_demand_model_overrides(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    s1 = sector(make, "a", 10, 2.0, 10.0, name="A")
    s2 = sector(make, "b", 10, 2.0, 10.0, name="B")
    body = {"overrides": [
        {"sector_id": s1.id, "volume_mt": 20},                        # volume only
        {"sector_id": s2.id, "volume_mt": 0.0, "intensity_tco2_per_t": 5.0},  # zero is a real override
    ]}
    rows = {r["sector_key"]: r for r in client.post("/api/india/demand-model", json=body, headers=ha).json()["sectors"]}
    assert (rows["a"]["volume_mt"], rows["a"]["intensity_tco2_per_t"]) == (20, 2.0)
    assert rows["a"]["illustrative_abatement_pool_mt_co2e"] == 4.0
    assert (rows["b"]["volume_mt"], rows["b"]["intensity_tco2_per_t"]) == (0.0, 5.0)
    assert rows["b"]["illustrative_abatement_pool_mt_co2e"] == 0.0


def test_missing_target_reduction_counts_as_zero(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    sector(make, "a", 10, 2.0, None)
    b = client.post("/api/india/demand-model", json={}, headers=ha).json()
    assert b["sectors"][0]["target_reduction_pct_avg"] == 0.0
    assert b["sectors"][0]["illustrative_abatement_pool_mt_co2e"] == 0.0
    assert b["sectors"][0]["baseline_emissions_mt_co2e"] == 20.0


def test_gap_analysis_splits_near_term_aspirational_and_excluded(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    sector(make, "a", 100, 1.0, 10.0)  # demand 10.0
    act = activity(make)
    supply(make, act, 2.5, models.FigureType.AWARDED_OPERATIONAL)
    supply(make, act, 1.25, models.FigureType.CURRENT_ACTUAL)
    supply(make, act, 40.0, models.FigureType.ASPIRATIONAL_TARGET)
    supply(make, act, None, models.FigureType.ASPIRATIONAL_TARGET, label="ccus")
    b = client.post("/api/india/gap-analysis", json={}, headers=ha).json()
    assert b["total_demand_mt_co2e"] == 10.0
    assert b["total_near_term_supply_mt_co2e"] == 3.75
    assert b["total_aspirational_supply_mt_co2e"] == 40.0
    assert b["near_term_gap_mt_co2e"] == 6.25
    assert b["supply_rows_excluded_no_conversion"] == ["ccus (src)"]
    assert "aspirational_target" in b["supply_methodology_note"]


def test_gap_analysis_respects_overrides_and_can_go_negative(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    s = sector(make, "a", 100, 1.0, 10.0)
    supply(make, activity(make), 8.0, models.FigureType.CURRENT_ACTUAL)
    b = client.post("/api/india/gap-analysis", json={"overrides": [{"sector_id": s.id, "volume_mt": 10}]}, headers=ha).json()
    assert b["total_demand_mt_co2e"] == 1.0
    assert b["near_term_gap_mt_co2e"] == -7.0


def test_simple_listings_are_ordered(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    a1 = activity(make, "z-act")
    cat = list(models.Article6Category)
    make.add(models.Article6EligibleActivity(category=cat[-1], name="last-cat"))
    cats = [x["category"] for x in client.get("/api/india/article6-activities", headers=ha).json()]
    assert cats == sorted(cats)
    for market in ("ZMarket", "AMarket"):
        make.add(models.IndiaCarbonPriceComparison(market=market, instrument="i", price_native=1, currency="X",
                                                   price_date=date(2026, 1, 1), source_confidence=SC.PRIMARY))
    assert [x["market"] for x in client.get("/api/india/carbon-prices", headers=ha).json()] == ["AMarket", "ZMarket"]
    supply(make, activity(make, "second"), 1, models.FigureType.CURRENT_ACTUAL)
    supply(make, a1, 1, models.FigureType.CURRENT_ACTUAL)
    ids = [x["activity_id"] for x in client.get("/api/india/supply-capacity", headers=ha).json()]
    assert ids == sorted(ids)
    for tech in ("Wind", "Solar"):
        make.add(models.CreditBenchmark(technology=tech, region="r", methodology="m", source_name="s", source_confidence=SC.MODELED))
    assert [x["technology"] for x in client.get("/api/india/credit-benchmarks", headers=ha).json()] == ["Solar", "Wind"]
    for prod, period in [("B", "2"), ("B", "1"), ("A", "9")]:
        make.add(models.IndiaCbamExportExposure(product_category=prod, period=period, source_name="s", source_confidence=SC.PRIMARY))
    rows = client.get("/api/india/cbam-export-exposure", headers=ha).json()
    assert [(r["product_category"], r["period"]) for r in rows] == [("A", "9"), ("B", "1"), ("B", "2")]


def benchmark(make, **kw):
    base = dict(technology="Solar", region="IN", methodology="ACM0002", source_name="s", source_confidence=SC.MODELED)
    base.update(kw)
    return make.add(models.CreditBenchmark(**base))


def test_capacity_to_credits_full_benchmark(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    b = benchmark(make, mwh_per_mw_per_year=1750.0, grid_emission_factor_tco2_per_mwh=0.7, tco2e_per_mw_per_year=1225.0)
    r = client.post("/api/india/capacity-to-credits", json={"benchmark_id": b.id, "capacity_mw": 10.5}, headers=ha).json()
    assert r["estimated_annual_mwh"] == 18375.0
    assert r["estimated_annual_tco2e"] == 12862.5
    assert r["capacity_mw"] == 10.5
    assert r["benchmark"]["technology"] == "Solar"
    assert r["note"].startswith("10.5 MW x 1750.0 MWh/MW/yr x 0.7 tCO2/MWh (ACM0002).")


def test_capacity_to_credits_missing_factors_give_none_and_question_marks(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    b = benchmark(make)
    r = client.post("/api/india/capacity-to-credits", json={"benchmark_id": b.id, "capacity_mw": 5}, headers=ha).json()
    assert r["estimated_annual_mwh"] is None and r["estimated_annual_tco2e"] is None
    assert "x ? MWh/MW/yr x ? tCO2/MWh" in r["note"]


def test_capacity_to_credits_zero_values_are_not_treated_as_missing(client, make, two_tenants):
    (_, _, _, ha), _ = two_tenants
    b = benchmark(make, mwh_per_mw_per_year=0.0, tco2e_per_mw_per_year=0.0)
    r = client.post("/api/india/capacity-to-credits", json={"benchmark_id": b.id, "capacity_mw": 5}, headers=ha).json()
    assert (r["estimated_annual_mwh"], r["estimated_annual_tco2e"]) == (0.0, 0.0)


def test_capacity_to_credits_unknown_benchmark(client, two_tenants):
    (_, _, _, ha), _ = two_tenants
    r = client.post("/api/india/capacity-to-credits", json={"benchmark_id": 99, "capacity_mw": 1}, headers=ha)
    assert (r.status_code, r.json()["detail"]) == (404, "Benchmark not found")
