"""Seed tables: credit benchmarks (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .tables_india_supply import PRIMARY, SECONDARY

# ---------------- Credit benchmarks: capacity -> credits, per technology ----------------
# Grounded in the REAL MRV formula (CDM ACM0002 / Verra VMR0017, adopted as-is by Gold
# Standard): baseline emissions = actual metered generation (MWh) x grid emission factor
# (tCO2/MWh). No registry publishes a default capacity factor — it's a project-specific
# estimate, not a methodology parameter — so capacity_factor_pct below is the best
# available REAL figure: either derived from MNRE's own official capacity+generation
# statistics (Renewable Energy Statistics 2024-25), an official MNRE/CERC regulatory
# tariff-setting benchmark, or a real operating project's observed output. Sourced from
# a Sept 2026 research pass; see docs/INDIA_CCTS_SOURCES.md for full derivation and caveats.
ACM0002_VMR0017 = "CDM ACM0002 / Verra VMR0017 (adopted as-is by Gold Standard): metered generation x grid emission factor"

credit_benchmarks = [
    dict(
        technology="Solar PV", region="India (national fleet average, FY2024-25)",
        capacity_factor_pct=17.5, mwh_per_mw_per_year=1530,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1126,
        methodology=ACM0002_VMR0017,
        source_name="MNRE Renewable Energy Statistics 2024-25 (capacity+generation, CUF derived) + CEA CO2 Baseline Database v21.0 (grid factor)",
        source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
        source_confidence=PRIMARY,
        notes="CUF is DERIVED by dividing MNRE's official FY2024-25 generation by average installed "
        "capacity — not an officially-published CUF table (none was found). Blends old+new plants "
        "and all site qualities; individual projects range ~14-26%+.",
    ),
    dict(
        technology="Solar PV", region="India (MNRE/CERC regulatory tariff-setting benchmark)",
        capacity_factor_pct=19.0, mwh_per_mw_per_year=1664,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1225,
        methodology=ACM0002_VMR0017,
        source_name="MNRE/CERC regulatory CUF benchmark used in tariff determination",
        source_url=None,
        source_confidence=SECONDARY,
        notes="The 19% figure is widely cited as the regulatory benchmark used in Indian solar tariff "
        "determinations; CERC's Renewable Energy Tariff Regulations 2024 is the likely primary source "
        "but was not fetched directly in this research pass.",
    ),
    dict(
        technology="Solar PV", region="India — Kamuthi Solar Park, Tamil Nadu (real operating project)",
        capacity_factor_pct=23.8, mwh_per_mw_per_year=2083,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1533,
        methodology=ACM0002_VMR0017,
        source_name="Kamuthi Solar Power Project (648 MWp, ~1.35 TWh/yr observed)",
        source_url="https://en.wikipedia.org/wiki/Kamuthi_Solar_Power_Project",
        source_confidence=SECONDARY,
        notes="A high-performing tracker-equipped real project, shown to illustrate the real range "
        "above the national fleet average — not a typical/default figure.",
    ),
    dict(
        technology="Onshore wind", region="India (national fleet average, FY2024-25)",
        capacity_factor_pct=19.8, mwh_per_mw_per_year=1735,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1277,
        methodology=ACM0002_VMR0017,
        source_name="MNRE Renewable Energy Statistics 2024-25 (capacity+generation, CUF derived) + CEA CO2 Baseline Database v21.0",
        source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
        source_confidence=PRIMARY,
        notes="Derived the same way as the solar fleet average. Site-level range is wide (~12-30%+) — "
        "older CDM-era Tamil Nadu/Gujarat sites averaged only ~11.8-18.5%, modern tall-tower turbines "
        "in good wind-class sites do meaningfully better.",
    ),
    dict(
        technology="Small hydro", region="India (national fleet average, FY2024-25)",
        capacity_factor_pct=26.2, mwh_per_mw_per_year=2290,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1685,
        methodology=ACM0002_VMR0017,
        source_name="MNRE Renewable Energy Statistics 2024-25",
        source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
        source_confidence=PRIMARY,
        notes="Derived the same way as solar/wind fleet averages.",
    ),
    dict(
        technology="Biomass / bagasse / waste-to-energy power", region="India (national fleet average, FY2024-25)",
        capacity_factor_pct=16.2, mwh_per_mw_per_year=1415,
        grid_emission_factor_tco2_per_mwh=0.736, tco2e_per_mw_per_year=1041,
        methodology=ACM0002_VMR0017,
        source_name="MNRE Renewable Energy Statistics 2024-25",
        source_url="https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/11/202511061627678782.pdf",
        source_confidence=PRIMARY,
        notes="MNRE's 'bio-power' category conflates biomass, bagasse cogeneration, and "
        "waste-to-energy — a true biomass-only figure would differ. Some biomass sub-types may also "
        "need a small project-emissions (PEy) deduction for fossil co-firing/transport, not applied here.",
    ),
    dict(
        technology="Offshore wind", region="International (no operational India project to derive a local figure)",
        capacity_factor_pct=44.0, mwh_per_mw_per_year=3854,
        grid_emission_factor_tco2_per_mwh=None, tco2e_per_mw_per_year=None,
        methodology=ACM0002_VMR0017,
        source_name="Real operating farms: Norther (Belgium) 43.1%, Alpha Ventus (Germany) 42-42.7%, European offshore fleet avg ~45.8%",
        source_url="https://en.wikipedia.org/wiki/Norther_Offshore_Wind_Farm",
        source_confidence=SECONDARY,
        notes="Deliberately left without a tCO2e/MW figure: the grid emission factor to multiply by "
        "depends entirely on which country's grid the project sits under — there's no single 'global "
        "offshore' EF. Use the mwh_per_mw_per_year figure with whatever host-country grid factor applies.",
    ),
]
