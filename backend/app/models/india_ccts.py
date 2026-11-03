"""Module 7: India CCTS and related market statistics."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import (
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import db_enum


# --------------------------------------------------------------------------
# Module 7: India CCTS — obligated-sector GEI targets (demand side),
# Article 6.2 eligible activities (supply side), and comparative Asian
# compliance-carbon pricing. Sourced from a research pass over BEE/MoEFCC/
# ICAP/PIB-secondary reporting — NOT from a primary gazette text (see each
# row's source_confidence + docs/INDIA_CCTS_SOURCES.md for caveats). Where
# official tCO2e figures don't exist (confirmed data gap — see docs), the
# "demand" figure is an explicitly-labeled illustrative model, not an
# official number: obligated_entities/target% are sourced, production
# volume/intensity defaults are editable assumptions.
# --------------------------------------------------------------------------
class GeiStatus(str, enum.Enum):
    FINAL = "final"
    DRAFT = "draft"
    CONTESTED = "contested"  # sources disagree on whether this is finalized


class SourceConfidence(str, enum.Enum):
    PRIMARY = "primary"  # a gazette/S.O./G.S.R. text or official portal, directly cited
    SECONDARY = "secondary"  # reputable secondary reporting (ICAP, law firm briefs, press) citing the primary source
    MODELED = "modeled"  # no official figure exists; this is an illustrative estimate


class IndiaCctsSector(Base):
    __tablename__ = "india_ccts_sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[GeiStatus] = mapped_column(db_enum(GeiStatus), nullable=False)
    notification_ref: Mapped[str] = mapped_column(String, nullable=True)
    notification_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    baseline_year: Mapped[str] = mapped_column(String, default="FY2023-24")
    compliance_years: Mapped[str] = mapped_column(String, default="FY2025-26, FY2026-27")
    obligated_entities_est: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_reduction_pct_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_reduction_pct_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_reduction_pct_avg: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Illustrative demand-model defaults — editable via the API, not official BEE data:
    default_volume_mt: Mapped[float] = mapped_column(Float, default=0.0)  # annual sector output, illustrative
    default_intensity_tco2_per_t: Mapped[float] = mapped_column(Float, default=0.0)  # baseline emission intensity
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    source_note: Mapped[str] = mapped_column(String, nullable=True)


class Article6Category(str, enum.Enum):
    MITIGATION = "mitigation"
    ALTERNATE_MATERIALS = "alternate_materials"
    REMOVAL = "removal"


class Article6EligibleActivity(Base):
    """India's MoEFCC/NDAIAPA list of activities eligible for Article 6.2 ITMO
    transfer (finalized 17 Feb 2023) — the supply side. No official aggregate
    pipeline volume (tCO2e) is published for any of these (confirmed data gap).

    Also carries one deliberately domestic-only row (ethanol/1G biofuel) — NOT
    on MoEFCC's list, kept here so the international-vs-domestic distinction is
    explicit in the model rather than a silent omission. See
    docs/INDIA_CCTS_SOURCES.md for the full investigation."""

    __tablename__ = "article6_eligible_activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[Article6Category] = mapped_column(db_enum(Article6Category), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    also_ccts_offset_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    internationally_tradeable: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class IndiaCarbonPriceComparison(Base):
    """Comparative compliance-carbon pricing: Korea K-ETS, China national ETS,
    Japan (J-Credit + GX-ETS corridor), EUA for context."""

    __tablename__ = "india_carbon_price_comparison"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    market: Mapped[str] = mapped_column(String, nullable=False)
    instrument: Mapped[str] = mapped_column(String, nullable=False)
    price_native: Mapped[float] = mapped_column(Float, nullable=False)
    price_native_high: Mapped[float | None] = mapped_column(Float, nullable=True)  # for a corridor/band
    currency: Mapped[str] = mapped_column(String, nullable=False)
    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    trend_note: Mapped[str] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)


class FigureType(str, enum.Enum):
    ASPIRATIONAL_TARGET = "aspirational_target"  # e.g. a 2030 policy goal, not yet built
    AWARDED_OPERATIONAL = "awarded_operational"  # capacity actually awarded/under construction/operating now
    CURRENT_ACTUAL = "current_actual"  # a measured current-year figure (e.g. cumulative PAT savings to date)


class IndiaSupplyCapacity(Base):
    """Bottom-up supply-side capacity for each Article 6.2-eligible activity,
    sourced from MNRE/MoPNG/PIB/CEA/BEE records — a proxy for potential credit
    supply, since no official Article 6.2 pipeline volume is published. Capacity
    (GW/MMT/plant count/etc.) is converted to potential avoided tCO2e/year where
    a defensible physical conversion exists (documented in conversion_note);
    where it doesn't (e.g. diffuse "BAT for hard-to-abate"), potential_avoided_mt_co2e
    stays null and the row is excluded from the gap-analysis total, not zero-filled."""

    __tablename__ = "india_supply_capacity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    activity_id: Mapped[int] = mapped_column(ForeignKey("article6_eligible_activities.id"))
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    figure_type: Mapped[FigureType] = mapped_column(db_enum(FigureType), nullable=False)
    as_of_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    conversion_note: Mapped[str] = mapped_column(String, nullable=True)
    potential_avoided_mt_co2e: Mapped[float | None] = mapped_column(Float, nullable=True)

    activity: Mapped[Article6EligibleActivity] = relationship()


class CreditBenchmark(Base):
    """Per-technology capacity -> credits benchmark, i.e. 'how many tCO2e/MW/year',
    grounded in the real MRV formula used by CDM ACM0002 / Verra's VMR0017 (which
    superseded ACM0002/AMS-I.D for VCS from Apr 2026) and adopted as-is by Gold
    Standard: baseline emissions = actual metered generation (MWh) x grid emission
    factor (tCO2/MWh). No registry publishes a fixed default capacity factor —
    that's a project-specific estimate, not a methodology parameter — so
    capacity_factor_pct here is the best available REAL benchmark (an official
    MNRE/CERC figure, or an India national fleet average derived from MNRE's own
    capacity+generation statistics) rather than an invented assumption, with each
    row's confidence and derivation documented in `notes`."""

    __tablename__ = "credit_benchmarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    technology: Mapped[str] = mapped_column(String, nullable=False)
    region: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "India (national fleet avg)"
    capacity_factor_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    mwh_per_mw_per_year: Mapped[float | None] = mapped_column(Float, nullable=True)
    grid_emission_factor_tco2_per_mwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    tco2e_per_mw_per_year: Mapped[float | None] = mapped_column(Float, nullable=True)
    methodology: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "CDM ACM0002 / Verra VMR0017"
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str] = mapped_column(String, nullable=True)


class IndiaCbamExportExposure(Base):
    """India's ACTUAL export exposure to EU CBAM, by product category and year --
    sourced from Lok Sabha Unstarred Questions (Ministry of Steel, JPC data), PIB,
    and GTRI (Global Trade Research Initiative) analysis. Distinct from the toy
    CbamGoodsImport/CbamDeclarant demo data elsewhere in this platform, which models
    a generic EU importer's workflow, not India's real export exposure. India's
    official Tradestat/DGCIS portal (tradestat.commerce.gov.in) is a JS-only form
    with no scrapable data endpoint -- confirmed directly, not assumed -- so this
    is built from parliamentary answers and think-tank analysis instead."""

    __tablename__ = "india_cbam_export_exposure"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_category: Mapped[str] = mapped_column(String, nullable=False)
    hs_chapter: Mapped[str] = mapped_column(String, nullable=True)
    period: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "FY2023-24"
    export_value_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    export_volume_tonnes: Mapped[float | None] = mapped_column(Float, nullable=True)
    yoy_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class ShippingEtsComplianceCost(Base):
    """What EU ETS maritime compliance actually costs shipping companies -- real
    industry-wide figures, distinct from the toy Vessel/Voyage/EmissionReport demo
    data elsewhere in this module, which models one tenant's own MRV workflow, not
    the sector-wide cost picture. Sourced primarily from the European Commission's
    own first monitoring report on the ETS maritime extension (COM(2025) 110 final,
    18 Mar 2025), which draws on THETIS-MRV data directly -- the closest thing to
    an official cost figure that exists for this still-new (Jan 2024) scheme."""

    __tablename__ = "shipping_ets_compliance_cost"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "aggregate_cost", "pass_through", "route_case_study", "context", "projection"
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "2024 (40% phase-in)"
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "EUR million", "%", "EUR/TEU"
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class GlobalCarbonMarketStat(Base):
    """How big the global carbon-credit market actually is, and who has what share of
    it -- market-wide reference data, not tenant-scoped, same pattern as
    IndiaCbamExportExposure / ShippingEtsComplianceCost. Deliberately covers BOTH
    compliance markets (EU ETS, China ETS, etc. -- mandatory cap-and-trade) and the
    voluntary carbon market (VCM), because the two are wildly different in scale and
    conflating them is a common source of confusion: compliance markets are the
    overwhelming majority of global carbon-market value. The VCM figures here are
    primary (read directly from Ecosystem Marketplace/Forest Trends' State of the
    Voluntary Carbon Market 2025); the compliance-market figures are secondary
    (World Bank State and Trends of Carbon Pricing 2025, via search synthesis, not
    a primary document read directly in this session) -- source_confidence per row
    reflects this honestly rather than treating all rows as equally solid."""

    __tablename__ = "global_carbon_market_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "compliance_market", "vcm_headline", "vcm_category_share", "context"
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class EuaTradingMarketStat(Base):
    """What the REAL EUA/carbon-derivatives trading market looks like, as a reality
    check next to this page's own simulated order book (a random-walk demo price
    series starting at EUR68, not a live feed). Same market-wide reference-data
    pattern as IndiaCbamExportExposure / ShippingEtsComplianceCost /
    GlobalCarbonMarketStat. Most rows are PRIMARY -- read directly from ICE's own
    24 Jan 2025 press release ("ICE Announces Record Environmental Market Trading
    in 2024") -- with 2025-year figures and qualitative market-structure notes
    marked SECONDARY where they come from search synthesis rather than a document
    read directly this session."""

    __tablename__ = "eua_trading_market_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "ice_trading_volume", "market_structure", "context"
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class EtsCoreSystemStat(Base):
    """What the EU ETS system actually looks like at full scale, next to this page's
    own 2-3-installation demo. Same market-wide reference-data pattern as the other
    three additions this session. All rows are SECONDARY: sourced via ICAP (the
    International Carbon Action Partnership's EU ETS policy summary, a well-
    maintained tracker used elsewhere in this platform for India CCTS research) and
    the EEA's own EU ETS data-viewer page, both via search synthesis/WebFetch
    summarization rather than a primary document read page-by-page this session --
    marked honestly rather than inflated to primary."""

    __tablename__ = "ets_core_system_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "system_scale", "allocation", "market_stability_reserve", "compliance", "context"
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)


class VerificationIntegrityStat(Base):
    """What real MRV/verification integrity looks like -- both the failure mode
    (Verra's 2023 REDD+ "phantom credits" controversy, a landmark and still-
    contested case study directly on point for a verification/audit page) and the
    market's institutional response (ICVCM's Core Carbon Principles labeling
    framework). Same market-wide reference-data pattern as the other four
    additions this session. All rows SECONDARY -- via search synthesis, not a
    primary document read directly this session -- and the Verra rows are
    additionally CONTESTED (Verra publicly disputes the investigation's framing),
    so this is flagged in both the data and the UI rather than presented as
    settled fact."""

    __tablename__ = "verification_integrity_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, nullable=False)  # e.g. "integrity_controversy", "integrity_response"
    metric_label: Mapped[str] = mapped_column(String, nullable=False)
    period: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String, nullable=False)
    source_name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_confidence: Mapped[SourceConfidence] = mapped_column(db_enum(SourceConfidence), nullable=False)
    notes: Mapped[str | None] = mapped_column(String, nullable=True)
