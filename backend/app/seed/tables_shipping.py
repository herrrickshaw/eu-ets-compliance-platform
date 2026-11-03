"""Seed tables: shipping (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .. import models

routes = [
    ("Rotterdam", "Hamburg", True, 280, 45),
    ("Hamburg", "Shanghai", False, 10_500, 1_850),
    ("Shanghai", "Rotterdam", False, 11_200, 1_920),
    ("Rotterdam", "Piraeus", True, 3_100, 520),
    ("Piraeus", "Istanbul", False, 380, 60),
]

# ---- Real EU ETS maritime compliance cost, distinct from the toy vessel/voyage demo above ----
# Sourced primarily from the European Commission's own first monitoring report on the ETS
# maritime extension, COM(2025) 110 final (18 Mar 2025), read directly -- drawn from THETIS-MRV
# data, the closest thing to an official industry-wide cost figure that exists for this scheme.
_P, _S, _M = models.SourceConfidence.PRIMARY, models.SourceConfidence.SECONDARY, models.SourceConfidence.MODELED

_COM_2025_110 = "https://climate.ec.europa.eu/document/download/1bb8387b-bdc4-4489-9d76-7ff30239704d_en?filename=First+report+on+the+implementation+of+the+ETS+extension+to+maritime+transport.pdf"

ets_cost = [
    dict(category="aggregate_cost", metric_label="Total EU ETS allowance cost, EU maritime sector",
         period="2024 (40% phase-in, at 2023 activity levels)", value=2200, unit="EUR million",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="The headline figure: ~34 million EUAs surrendered at an average price of EUR "
         "64/tCO2 (2024) implies ~EUR 2,200 million to acquire allowances industry-wide. This is "
         "the ONLY year with a Commission-published aggregate cost so far -- 2025 (70% phase-in) "
         "and 2026+ (100%) figures are not yet published as of this seed data's research date."),
    dict(category="aggregate_cost", metric_label="EU ETS allowances (EUAs) surrendered, EU maritime sector",
         period="2024", value=34, unit="million EUAs",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes="At 40% phase-in of verified emissions."),
    dict(category="aggregate_cost", metric_label="Average EUA price used in this cost estimate",
         period="2024", value=64, unit="EUR/tCO2",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes="The Commission's own assumed average price for the year, not a spot quote."),
    dict(category="aggregate_cost", metric_label="Increase in total shipping costs attributable to ETS",
         period="2024 (40% phase-in)", value=3.7, unit="%",
         source_name="European Commission, COM(2025) 110 final, Section 6", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="Against total shipping costs (fuel, staff, port fees, capital costs, etc.), "
         "assuming no energy-efficiency or emissions-reduction measures are taken -- i.e. an "
         "upper-bound estimate of the unmitigated cost impact. Varies greatly by vessel category "
         "depending on intra- vs extra-EU emissions share."),
    dict(category="context", metric_label="Total verified CO2 emissions, EU ETS maritime scope",
         period="2024 (first reporting year)", value=89.8, unit="Mt CO2",
         source_name="European Commission (secondary reporting, THETIS-MRV-derived figure)",
         source_url="https://climate.ec.europa.eu/eu-action/transport/reducing-emissions-shipping-sector_en",
         source_confidence=_S,
         notes="Reported by >13,000 vessels and >3,000 shipping companies in the scheme's first "
         "year. Cross-checks reasonably with the aggregate_cost rows above: 34 million EUAs "
         "surrendered / 40% phase-in implies ~85 Mt of full-scope emissions, in the right range "
         "given the different activity-year assumptions each figure uses."),
    dict(category="pass_through", metric_label="Container freight ETS surcharge pass-through (deep-sea) -- low end",
         period="2024", value=1, unit="% of freight rate",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes="Range 1-5%; announced liner ETS surcharges fall in this band."),
    dict(category="pass_through", metric_label="Container freight ETS surcharge pass-through (deep-sea) -- high end",
         period="2024", value=5, unit="% of freight rate",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="For context, container freight rates overall grew ~120 percentage points from Oct "
         "2023 to Jun 2024, mostly due to the Red Sea crisis -- the ETS surcharge is a small "
         "fraction of total freight-rate movement in this period."),
    dict(category="pass_through", metric_label="Ferry/RoPax ticket price ETS impact -- low end",
         period="2024", value=3, unit="% of ticket price",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes="Range 3-11% across EU ferry routes analysed."),
    dict(category="pass_through", metric_label="Ferry/RoPax ticket price ETS impact -- high end",
         period="2024", value=11, unit="% of ticket price",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes=None),
    dict(category="pass_through", metric_label="Ferry ETS cost as share of total shipping cost (100% fossil-fuel routes)",
         period="2024", value=8, unit="% of total shipping cost",
         source_name="European Commission, COM(2025) 110 final, Section 6.2", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="For ferry routes with no territorial-continuity exemption. Expected to rise in "
         "2025/2026 as the phase-in percentage increases; no evidence yet (as of this report) of "
         "reduced service frequency to islands as a result."),
    dict(category="route_case_study", metric_label="Shanghai-Rotterdam containership (14,000 TEU) -- ETS cost via Cape of Good Hope reroute",
         period="2024 case study", value=145_000, unit="EUR per voyage",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="2015-built vessel, fossil fuels only, ~78% load factor assumed. Implies ~EUR "
         "10/TEU. Rerouting via the Cape (avoiding the Red Sea/Suez) is the longer, higher-fuel-"
         "burn path, hence the higher ETS cost than the Suez route below."),
    dict(category="route_case_study", metric_label="Shanghai-Rotterdam containership (14,000 TEU) -- ETS cost via Suez Canal",
         period="2024 case study", value=106_000, unit="EUR per voyage",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes="Same vessel/assumptions as the Cape route above. Implies ~EUR 7/TEU."),
    dict(category="route_case_study", metric_label="Actual liner ETS surcharge, Asia to North Europe (average)",
         period="2024", value=30, unit="EUR/TEU",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P,
         notes="Announced by liner operators. Notably HIGHER than the Commission's own computed "
         "per-route cost (~EUR 7-10/TEU for the comparable Shanghai-Rotterdam case study above) -- "
         "the Commission's own reading is that liner operators can fully pass through, and in some "
         "cases over-recover relative to, their actual EUA cost via these surcharges."),
    dict(category="route_case_study", metric_label="Actual liner ETS surcharge, North Europe to Asia (reverse direction)",
         period="2024", value=20, unit="EUR/TEU",
         source_name="European Commission, COM(2025) 110 final, Section 6.1", source_url=_COM_2025_110,
         source_confidence=_P, notes=None),
    dict(category="projection", metric_label="Illustrative full-phase-in cost, holding 2024 emissions/price constant",
         period="2026+ (100% phase-in, NOT an official projection)", value=5500, unit="EUR million",
         source_name="This platform's own extrapolation, not a Commission figure", source_url=None,
         source_confidence=_M,
         notes="A simple x2.5 scaling of the EUR 2,200M / 40%-phase-in 2024 figure to 100% "
         "phase-in, holding both emissions volume and EUA price constant at their 2024 levels. "
         "The Commission's own report explicitly declines to project this, noting 'higher "
         "increases are anticipated in 2025 and 2026, linked to the phase-in approach' without a "
         "number -- real 2025/2026 costs will also depend on the EUA price path (volatile, "
         "roughly EUR 60-120/t through 2025-26) and on FuelEU Maritime stacking on top of ETS, "
         "neither of which this extrapolation accounts for. Treat as an order-of-magnitude "
         "orientation figure only, not a forecast."),
]
