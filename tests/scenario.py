"""Deterministic API scenario used to characterise the backend (seeded DB, fixed request order).

`run_scenario(client)` returns a JSON-able dict of every response; the committed golden file was
captured from the pre-refactor code, and `test_characterisation.py` asserts the refactor matches it.
"""
from __future__ import annotations

import re
from typing import Any

PASSWORD = "demo1234"
ORG_NAMES = {
    "importer1": "Iberia Metals Import SL",
    "importer2": "Baltic Fertilizer Traders",
    "shipco": "Hanseatic Container Lines",
    "tankerco": "Aegean Tanker Group",
    "trader1": "Meridian Carbon Trading LLP",
    "trader2": "Nordpool Emissions Desk",
}
VOLATILE = {"created_at", "executed_at", "submitted_at", "occurred_at", "access_token"}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items() if k not in VOLATILE}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    return obj


def run_scenario(client) -> dict:
    out: dict = {}
    headers: dict = {}

    def login(key: str) -> dict:
        r = client.post("/api/auth/login", json={"email": f"demo@{_slug(ORG_NAMES[key])}.example", "password": PASSWORD})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    def call(label: str, method: str, url: str, **kw) -> Any:
        r = client.request(method, url, headers=headers, **kw)
        body = r.json() if r.content else None
        if label.startswith(("trading.orders", "trading.trades")) and isinstance(body, list):
            body = sorted(body, key=lambda row: row["id"])  # created_at ties make server order unstable
        out[label] = {"status": r.status_code, "body": _scrub(body)}
        return body

    # ---- India CCTS (global reference data) ----
    headers = login("trader1")
    sectors = call("india.sectors", "GET", "/api/india/sectors")
    call("india.demand.default", "POST", "/api/india/demand-model", json={"overrides": []})
    overrides = [
        {"sector_id": sectors[0]["id"], "volume_mt": 123.4},
        {"sector_id": sectors[1]["id"], "intensity_tco2_per_t": 2.5},
        {"sector_id": sectors[2]["id"], "volume_mt": 10.0, "intensity_tco2_per_t": 0.0},
    ]
    call("india.demand.overrides", "POST", "/api/india/demand-model", json={"overrides": overrides})
    call("india.gap.default", "POST", "/api/india/gap-analysis", json={"overrides": []})
    call("india.gap.overrides", "POST", "/api/india/gap-analysis", json={"overrides": overrides})
    call("india.article6", "GET", "/api/india/article6-activities")
    call("india.prices", "GET", "/api/india/carbon-prices")
    call("india.supply", "GET", "/api/india/supply-capacity")
    call("india.cbam_exposure", "GET", "/api/india/cbam-export-exposure")
    bms = call("india.benchmarks", "GET", "/api/india/credit-benchmarks")
    for b in bms:
        call(f"india.capacity.{b['id']}", "POST", "/api/india/capacity-to-credits", json={"benchmark_id": b["id"], "capacity_mw": 250.5})
    call("india.capacity.missing", "POST", "/api/india/capacity-to-credits", json={"benchmark_id": 99999, "capacity_mw": 1})

    # ---- Trading ----
    insts = call("trading.instruments", "GET", "/api/trading/instruments")
    call("trading.orders.initial", "GET", "/api/trading/orders")
    call("trading.market_reality", "GET", "/api/trading/market-reality")
    for i in insts:
        call(f"trading.prices.{i['id']}", "GET", f"/api/trading/prices/{i['id']}")
    eua = insts[0]["id"]
    orgs = call("orgs", "GET", "/api/orgs")
    by_name = {o["name"]: o["id"] for o in orgs}
    t1, t2 = by_name[ORG_NAMES["trader1"]], by_name[ORG_NAMES["trader2"]]
    call("trading.positions.t1.before", "GET", "/api/trading/positions")
    placed = []
    for label, org, side, qty, px in [
        ("sell_rest", t1, "sell", 100.0, 70.0),
        ("sell_rest2", t1, "sell", 50.0, 72.0),
        ("buy_no_cross", t1, "buy", 10.0, 1.0),
    ]:
        placed.append(call(f"trading.place.{label}", "POST", "/api/trading/orders",
                           json={"org_id": org, "instrument_id": eua, "side": side, "quantity": qty, "limit_price_eur": px}))
    cancel_id = placed[2]["id"]
    call("trading.cancel", "DELETE", f"/api/trading/orders/{cancel_id}")
    call("trading.cancel_again", "DELETE", f"/api/trading/orders/{cancel_id}")
    call("trading.cancel_missing", "DELETE", "/api/trading/orders/99999")
    call("trading.place.foreign_org", "POST", "/api/trading/orders",
         json={"org_id": t2, "instrument_id": eua, "side": "buy", "quantity": 1, "limit_price_eur": 1})
    call("trading.positions.t1.after", "GET", "/api/trading/positions")
    call("trading.positions.foreign", "GET", f"/api/trading/positions?org_id={t2}")
    headers = login("trader2")
    for label, side, qty, px in [("buy_partial", "buy", 120.0, 71.0), ("buy_sweep", "buy", 100.0, 80.0), ("sell_cross", "sell", 30.0, 60.0)]:
        call(f"trading.place.{label}", "POST", "/api/trading/orders",
             json={"org_id": t2, "instrument_id": eua, "side": side, "quantity": qty, "limit_price_eur": px})
    call("trading.orders.final", "GET", "/api/trading/orders")
    call("trading.orders.open", "GET", "/api/trading/orders?status=open")
    call("trading.trades", "GET", "/api/trading/trades")
    call("trading.trades.eua", "GET", f"/api/trading/trades?instrument_id={eua}")
    call("trading.positions.t2", "GET", "/api/trading/positions")

    # ---- CBAM ----
    headers = login("importer1")
    decls = call("cbam.declarants", "GET", "/api/cbam/declarants")
    dvs = call("cbam.default_values", "GET", "/api/cbam/default-values")
    call("cbam.phase_in", "GET", "/api/cbam/phase-in-schedule")
    call("cbam.imports.before", "GET", "/api/cbam/imports")
    call("cbam.declarations.before", "GET", "/api/cbam/declarations")
    d1 = decls[0]["id"]
    cn_codes = sorted({d["cn_code"] for d in dvs})
    countries = sorted({d["country"] for d in dvs})
    n = 0
    for cn in cn_codes:
        for ctry in countries[:3] + ["ZZ"]:
            n += 1
            call(f"cbam.import.default.{n}", "POST", "/api/cbam/imports",
                 json={"declarant_id": d1, "cn_code": cn, "country_of_origin": ctry, "quantity_t": 100.0 + n, "import_date": f"2026-0{1 + n % 9}-15"})
    call("cbam.import.unknown_cn", "POST", "/api/cbam/imports",
         json={"declarant_id": d1, "cn_code": "0000", "country_of_origin": "ZZ", "quantity_t": 5, "import_date": "2026-02-02"})
    call("cbam.import.actual", "POST", "/api/cbam/imports",
         json={"declarant_id": d1, "cn_code": cn_codes[0], "country_of_origin": "ZZ", "quantity_t": 40.0, "import_date": "2026-11-20",
               "actual_direct_emissions_t": 12.3456, "actual_indirect_emissions_t": 1.5})
    call("cbam.import.actual_direct_only", "POST", "/api/cbam/imports",
         json={"declarant_id": d1, "cn_code": cn_codes[0], "country_of_origin": "ZZ", "quantity_t": 40.0, "import_date": "2026-12-31",
               "actual_direct_emissions_t": 7.0})
    call("cbam.import.foreign_declarant", "POST", "/api/cbam/imports",
         json={"declarant_id": 99999, "cn_code": cn_codes[0], "country_of_origin": "ZZ", "quantity_t": 1, "import_date": "2026-01-01"})
    call("cbam.imports.after", "GET", "/api/cbam/imports")
    call("cbam.imports.filtered", "GET", f"/api/cbam/imports?declarant_id={d1}")
    for year in (2025, 2026):
        for q in (1, 2, 3, 4):
            call(f"cbam.reconcile.{year}.q{q}", "POST", f"/api/cbam/declarations/{d1}/{year}/{q}/reconcile")
    call("cbam.declarations.after", "GET", "/api/cbam/declarations")
    for y in (2025, 2026, 2030, 2034, 2040):
        call(f"cbam.demand.{y}", "GET", f"/api/cbam/demand-analysis?year={y}")
    for y in (2025, 2026):
        call(f"cbam.projection.{y}", "GET", f"/api/cbam/demand-projection?base_year={y}")
    headers = login("importer2")
    call("cbam.imports.other_tenant", "GET", "/api/cbam/imports")
    call("cbam.demand.other_tenant", "GET", "/api/cbam/demand-analysis?year=2026")
    call("cbam.reconcile.foreign", "POST", f"/api/cbam/declarations/{d1}/2026/1/reconcile")

    # ---- Shipping MRV ----
    for key in ("shipco", "tankerco"):
        headers = login(key)
        vessels = call(f"ship.{key}.vessels", "GET", "/api/shipping/vessels")
        call(f"ship.{key}.plans", "GET", "/api/shipping/monitoring-plans")
        call(f"ship.{key}.voyages", "GET", "/api/shipping/voyages")
        call(f"ship.{key}.reports.before", "GET", "/api/shipping/emission-reports")
        for v in vessels:
            for year in (2023, 2024, 2025, 2026):
                call(f"ship.{key}.submit.{v['id']}.{year}", "POST", "/api/shipping/emission-reports/submit",
                     json={"vessel_id": v["id"], "year": year})
        call(f"ship.{key}.reports.after", "GET", "/api/shipping/emission-reports")
    call("ship.missing_vessel", "POST", "/api/shipping/emission-reports/submit", json={"vessel_id": 99999, "year": 2024})
    call("ship.compliance_cost", "GET", "/api/shipping/ets-compliance-cost")
    return out
