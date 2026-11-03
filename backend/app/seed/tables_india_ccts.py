"""Seed tables: india ccts (illustrative demo data, see seed_data.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta  # noqa: F401

from .. import models

# ---------------- Module 7: India CCTS ----------------
# Sourced from a Sept 2026 research pass (BEE/MoEFCC/ICAP/secondary reporting —
# NOT a local repo, NOT a primary gazette text; see docs/INDIA_CCTS_SOURCES.md).
# obligated_entities_est / target_reduction_pct_* / status / notification_ref are
# sourced as noted per row. default_volume_mt / default_intensity_tco2_per_t are
# illustrative editable assumptions (steel/aluminium/cement/fertilizer intensities
# reused from this platform's own CBAM default-value table for consistency;
# others are rough order-of-magnitude estimates) — NOT official BEE figures.
india_sectors = [
    dict(
        key="aluminium", name="Aluminium", status=models.GeiStatus.FINAL,
        notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
        obligated_entities_est=None, target_reduction_pct_low=2.8, target_reduction_pct_high=7.06,
        target_reduction_pct_avg=4.9, default_volume_mt=4.1, default_intensity_tco2_per_t=10.15,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of a combined 282-entity announcement across 4 sectors (not broken out per "
        "sector in sources found). Intensity reused from this platform's CBAM aluminium default value.",
    ),
    dict(
        key="cement", name="Cement", status=models.GeiStatus.FINAL,
        notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
        obligated_entities_est=None, target_reduction_pct_low=4.7, target_reduction_pct_high=7.6,
        target_reduction_pct_avg=6.15, default_volume_mt=370, default_intensity_tco2_per_t=0.95,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Integrated plants ~2.7% / Grinding units ~6.6% per source; avg is the low-high "
        "midpoint. Part of the same combined 282-entity announcement. Intensity reused from this "
        "platform's CBAM cement default value.",
    ),
    dict(
        key="chlor_alkali", name="Chlor-Alkali", status=models.GeiStatus.FINAL,
        notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
        obligated_entities_est=None, target_reduction_pct_low=3.3, target_reduction_pct_high=11.0,
        target_reduction_pct_avg=6.5, default_volume_mt=4.5, default_intensity_tco2_per_t=1.8,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of the same combined 282-entity announcement. Volume/intensity are illustrative "
        "(no CBAM reference value available for this sector).",
    ),
    dict(
        key="pulp_paper", name="Pulp & Paper", status=models.GeiStatus.FINAL,
        notification_ref="G.S.R. 739(E)", notification_date=date(2025, 10, 8),
        obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=15.0,
        target_reduction_pct_avg=6.5, default_volume_mt=20, default_intensity_tco2_per_t=1.2,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of the same combined 282-entity announcement; low end of target range not "
        "found. Volume/intensity are illustrative.",
    ),
    dict(
        key="petroleum_refining", name="Petroleum Refining", status=models.GeiStatus.FINAL,
        notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
        obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
        target_reduction_pct_avg=3.1, default_volume_mt=254, default_intensity_tco2_per_t=0.3,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of a combined ~208-entity addition (petroleum refining + petrochemicals + "
        "textiles, not broken out individually) bringing the cumulative total to ~490 across 7 sectors. "
        "Volume/intensity are illustrative.",
    ),
    dict(
        key="petrochemicals", name="Petrochemicals", status=models.GeiStatus.FINAL,
        notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
        obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
        target_reduction_pct_avg=3.6, default_volume_mt=30, default_intensity_tco2_per_t=1.0,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of the same combined ~208-entity addition as petroleum refining/textiles. "
        "Volume/intensity are illustrative.",
    ),
    dict(
        key="textiles", name="Textiles", status=models.GeiStatus.FINAL,
        notification_ref="MoEFCC notification", notification_date=date(2026, 1, 16),
        obligated_entities_est=None, target_reduction_pct_low=None, target_reduction_pct_high=None,
        target_reduction_pct_avg=6.6, default_volume_mt=7, default_intensity_tco2_per_t=2.5,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="Part of the same combined ~208-entity addition as petroleum refining/petrochemicals. "
        "Volume/intensity are illustrative.",
    ),
    dict(
        key="iron_steel", name="Iron & Steel", status=models.GeiStatus.DRAFT,
        notification_ref="Revised draft (not yet final)", notification_date=date(2026, 6, 26),
        obligated_entities_est=255, target_reduction_pct_low=2.0, target_reduction_pct_high=5.0,
        target_reduction_pct_avg=3.5, default_volume_mt=145, default_intensity_tco2_per_t=2.93,
        source_confidence=models.SourceConfidence.SECONDARY,
        source_note="255 units across 10 states; draft made public 2 Jul 2026 with a 60-day objection "
        "window (~through end-Aug 2026) — NOT yet legally binding as of this seed. Criticized by Climate "
        "Risk Horizons as too weak. Intensity reused from this platform's CBAM steel (India) default value.",
    ),
    dict(
        key="fertilizer", name="Fertilizer", status=models.GeiStatus.CONTESTED,
        notification_ref=None, notification_date=None,
        obligated_entities_est=20, target_reduction_pct_low=None, target_reduction_pct_high=None,
        target_reduction_pct_avg=None, default_volume_mt=30, default_intensity_tco2_per_t=4.1,
        source_confidence=models.SourceConfidence.MODELED,
        source_note="Status is genuinely contested across sources: one claims final gazette notification "
        "8 Oct 2025 alongside 4 other sectors, but ICAP's detailed CCTS page lists only 7 finalized "
        "sectors and does NOT include fertilizer. No confirmed target % found — do not treat as final. "
        "~20 plants anticipated (NFL, RCF, IFFCO, FACT, GSFC, KRIBHCO, Chambal). Intensity reused from "
        "this platform's CBAM fertilizer default value (reasonably close to one source's modeled "
        "2.2-3.1 tCO2e/t baseline estimate).",
    ),
]

article6_activities = [
    ("re_storage", "Renewable energy with storage (stored component only)", models.Article6Category.MITIGATION, False),
    ("solar_thermal", "Solar thermal power", models.Article6Category.MITIGATION, False),
    ("offshore_wind", "Offshore wind", models.Article6Category.MITIGATION, False),
    ("green_hydrogen", "Green hydrogen", models.Article6Category.MITIGATION, False),
    ("cbg", "Compressed biogas", models.Article6Category.MITIGATION, False),
    ("mobility", "Emerging mobility / fuel cells", models.Article6Category.MITIGATION, False),
    ("energy_efficiency", "High-efficiency / high-end energy-efficiency technology", models.Article6Category.MITIGATION, True),
    ("saf", "Sustainable aviation fuel (SAF)", models.Article6Category.MITIGATION, False),
    ("bat_hard_to_abate", "Best Available Technologies (BAT) for hard-to-abate process improvement", models.Article6Category.MITIGATION, False),
    ("tidal", "Tidal / ocean thermal / salt-gradient / wave / current energy", models.Article6Category.MITIGATION, False),
    ("hvdc", "HVDC transmission paired with renewable energy projects", models.Article6Category.MITIGATION, False),
    ("green_ammonia", "Green ammonia", models.Article6Category.ALTERNATE_MATERIALS, False),
    ("ccus", "Carbon Capture, Utilization and Storage (CCUS)", models.Article6Category.REMOVAL, True),
]

india_prices = [
    dict(
        market="Korea", instrument="KAU (K-ETS)", price_native=13750, currency="KRW",
        price_usd=9.53, price_eur=8.80, price_date=date(2026, 3, 1),
        trend_note="Up ~33% YTD 2026; 2025 secondary-market avg was KRW 9,393 (~$6.60). Recovering "
        "after years of oversupply; 2026-2030 phase cuts the cap ~12% (2.54 bn tCO2e).",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
    dict(
        market="China", instrument="CEA (national ETS)", price_native=83.86, currency="CNY",
        price_usd=11.0, price_eur=10.5, price_date=date(2026, 8, 31),
        trend_note="Jan-Aug 2026 average, peaking near CNY 100 late Aug; +14.4% YoY vs 2025 full-year "
        "avg of CNY 73.3/t. Rising as metals/cement sectors are folded into the national ETS.",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
    dict(
        market="Japan", instrument="J-Credit (energy efficiency)", price_native=4800, currency="JPY",
        price_usd=32.0, price_eur=30.0, price_date=date(2026, 4, 7),
        trend_note="Platts assessment. Voluntary scheme; usable for up to 10% of GX-ETS compliance.",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
    dict(
        market="Japan", instrument="J-Credit (forestry)", price_native=5300, currency="JPY",
        price_usd=35.0, price_eur=33.0, price_date=date(2026, 4, 7),
        trend_note="Platts assessment; one exchange listing showed forestry J-Credit at JPY 4,400 in "
        "Jul 2026 — prices vary meaningfully by listing venue.",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
    dict(
        market="Japan", instrument="GX-ETS allowance (mandatory, FY2026 corridor)", price_native=1700,
        price_native_high=4300, currency="JPY", price_usd=None, price_eur=None, price_date=date(2026, 4, 1),
        trend_note="NOT an observed trade price — a government-set floor/ceiling corridor; trading was "
        "described as absent a week into the mandatory phase. Policymakers reportedly considering a "
        "JPY 4,000-6,000/t band by 2027. J-Credit is the more usable real/observed Japan proxy for now.",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
    dict(
        market="EU", instrument="EUA (context)", price_native=83.80, currency="EUR",
        price_usd=None, price_eur=83.80, price_date=date(2026, 9, 7),
        trend_note="Range ~EUR 75.5-83.8/t through Sept 2026 (EUR 83.80 = highest since Jul 2026). Some "
        "2026 full-year forecasts cite ~EUR 104/t average — an unverified analyst forecast, not spot.",
        source_confidence=models.SourceConfidence.SECONDARY,
    ),
]
