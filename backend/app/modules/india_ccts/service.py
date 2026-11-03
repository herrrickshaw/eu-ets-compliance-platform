"""Pure demand/supply/credit arithmetic for the India CCTS module (no DB access)."""
from __future__ import annotations

from typing import Iterable, Mapping, Optional

from ... import models, schemas


def compute_demand_rows(
    sectors: Iterable[models.IndiaCctsSector], overrides: Mapping[int, schemas.SectorAssumptionOverride]
) -> tuple[list[schemas.SectorDemandOut], float]:
    """Per-sector baseline emissions and abatement pool (Mt CO2e); returns (rows, unrounded total pool)."""
    rows = []
    total = 0.0
    for s in sectors:
        override = overrides.get(s.id)
        volume = override.volume_mt if override and override.volume_mt is not None else s.default_volume_mt
        intensity = (
            override.intensity_tco2_per_t
            if override and override.intensity_tco2_per_t is not None
            else s.default_intensity_tco2_per_t
        )
        target_pct = s.target_reduction_pct_avg or 0.0

        baseline_mt_co2e = volume * intensity
        pool_mt_co2e = baseline_mt_co2e * (target_pct / 100)
        total += pool_mt_co2e

        rows.append(
            schemas.SectorDemandOut(
                sector_id=s.id,
                sector_key=s.key,
                sector_name=s.name,
                status=s.status.value,
                volume_mt=volume,
                intensity_tco2_per_t=intensity,
                target_reduction_pct_avg=target_pct,
                baseline_emissions_mt_co2e=round(baseline_mt_co2e, 2),
                illustrative_abatement_pool_mt_co2e=round(pool_mt_co2e, 2),
            )
        )
    return rows, total


def split_supply(rows: Iterable[models.IndiaSupplyCapacity]) -> tuple[float, float, list[str]]:
    """Return (near_term_total, aspirational_total, excluded labels) in Mt CO2e."""
    near_term_total = 0.0
    aspirational_total = 0.0
    excluded: list[str] = []
    for row in rows:
        if row.potential_avoided_mt_co2e is None:
            excluded.append(f"{row.metric_label} ({row.source_name})")
        elif row.figure_type == models.FigureType.ASPIRATIONAL_TARGET:
            aspirational_total += row.potential_avoided_mt_co2e
        else:
            near_term_total += row.potential_avoided_mt_co2e
    return near_term_total, aspirational_total, excluded


def estimate_capacity_credits(
    benchmark: models.CreditBenchmark, capacity_mw: float
) -> tuple[Optional[float], Optional[float]]:
    """Return (annual MWh, annual tCO2e) for a capacity in MW from the benchmark's per-MW figures."""
    mwh = None
    tco2e = None
    if benchmark.mwh_per_mw_per_year is not None:
        mwh = round(capacity_mw * benchmark.mwh_per_mw_per_year, 2)
    if benchmark.tco2e_per_mw_per_year is not None:
        tco2e = round(capacity_mw * benchmark.tco2e_per_mw_per_year, 2)
    return mwh, tco2e
