"""
Shared data model for the whole platform.

Design borrows, deliberately, from real reference systems rather than inventing
a schema from scratch:
  - ETS core account/transaction shape  -> EU Union Registry
  - Shipping MRV workflow                -> EMSA THETIS-MRV state machine
  - CBAM sub-model split                 -> CBAM Transitional Registry
                                             (Trader Portal / Authorisation
                                             Management / Data Reconciliation)
  - Credit hierarchy + stage/verify/commit -> Chia-Network/cadt (CAD Trust)
  - Verification as a cross-cutting stage  -> cadt staged-write pattern,
                                             generalized across ETS/CBAM/credits
See docs/ARCHITECTURE.md for the full mapping and sources.
"""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def db_enum(enum_cls):
    """SQLAlchemy's Enum() stores the member .name by default; force .value
    (our lowercase strings) so API filters/schemas comparing against .value work."""
    return Enum(enum_cls, values_callable=lambda x: [e.value for e in x])


def _now() -> datetime:
    return datetime.utcnow()


# --------------------------------------------------------------------------
# Auth & multi-tenancy: every Organization belongs to exactly one Tenant
# (the billing/login boundary — a customer's account on the platform). A
# Tenant can in principle own several Organizations (a group with
# subsidiaries); the demo seeds one Tenant per Organization.
# --------------------------------------------------------------------------
class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    slug: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[UserRole] = mapped_column(db_enum(UserRole), default=UserRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    tenant: Mapped[Tenant] = relationship()


# --------------------------------------------------------------------------
# Shared: organizations — every actor in the system is one of these
# --------------------------------------------------------------------------
class OrgType(str, enum.Enum):
    ETS_OPERATOR = "ets_operator"
    SHIPPING_COMPANY = "shipping_company"
    CBAM_DECLARANT = "cbam_declarant"
    CREDIT_DEVELOPER = "credit_developer"
    TRADER = "trader"
    VERIFIER = "verifier"
    REGULATOR = "regulator"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    org_type: Mapped[OrgType] = mapped_column(db_enum(OrgType), nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=True)
    lei_or_eori: Mapped[str] = mapped_column(String, nullable=True)

    tenant: Mapped[Tenant] = relationship()


# --------------------------------------------------------------------------
# Module 1: EU ETS core (installations, allowances) — Union Registry shape
# --------------------------------------------------------------------------
class Installation(Base):
    __tablename__ = "installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    sector: Mapped[str] = mapped_column(String, nullable=False)  # e.g. power, steel, cement
    ets_scheme: Mapped[str] = mapped_column(String, default="EU_ETS_1")  # EU_ETS_1 | EU_ETS_2

    org: Mapped[Organization] = relationship()


class AccountType(str, enum.Enum):
    OPERATOR_HOLDING = "operator_holding"
    TRADING = "trading"
    NATIONAL_ADMIN = "national_admin"


class AllowanceAccount(Base):
    __tablename__ = "allowance_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    installation_id: Mapped[int | None] = mapped_column(ForeignKey("installations.id"), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(db_enum(AccountType), nullable=False)
    instrument: Mapped[str] = mapped_column(String, default="EUA")  # EUA | EUAA (aviation) | ETS2
    balance: Mapped[float] = mapped_column(Float, default=0.0)

    org: Mapped[Organization] = relationship()
    installation: Mapped[Installation | None] = relationship()


class AllowanceTxnType(str, enum.Enum):
    FREE_ALLOCATION = "free_allocation"
    PURCHASE = "purchase"
    SALE = "sale"
    SURRENDER = "surrender"
    TRANSFER = "transfer"


class AllowanceTransaction(Base):
    __tablename__ = "allowance_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("allowance_accounts.id"))
    counterparty_account_id: Mapped[int | None] = mapped_column(ForeignKey("allowance_accounts.id"), nullable=True)
    txn_type: Mapped[AllowanceTxnType] = mapped_column(db_enum(AllowanceTxnType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    price_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    compliance_year: Mapped[int] = mapped_column(Integer, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ComplianceStatus(Base):
    """One row per installation per compliance year — surrender-deadline tracking."""

    __tablename__ = "compliance_status"
    __table_args__ = (UniqueConstraint("installation_id", "year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    installation_id: Mapped[int] = mapped_column(ForeignKey("installations.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    verified_emissions_t: Mapped[float] = mapped_column(Float, nullable=False)
    free_allocation_t: Mapped[float] = mapped_column(Float, default=0.0)
    allowances_surrendered_t: Mapped[float] = mapped_column(Float, default=0.0)
    surrender_deadline: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String, default="open")  # open | compliant | short | penalized


# --------------------------------------------------------------------------
# Module 2: Shipping MRV — THETIS-MRV state machine
# --------------------------------------------------------------------------
class Vessel(Base):
    __tablename__ = "vessels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    imo_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    vessel_type: Mapped[str] = mapped_column(String, nullable=False)  # container, tanker, bulk, ...
    gross_tonnage: Mapped[float] = mapped_column(Float, nullable=False)

    org: Mapped[Organization] = relationship()


class MonitoringPlanStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class MonitoringPlan(Base):
    """THETIS-MRV step 1: ship-specific monitoring plan, Annex I template shape."""

    __tablename__ = "monitoring_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessels.id"))
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[MonitoringPlanStatus] = mapped_column(db_enum(MonitoringPlanStatus), default=MonitoringPlanStatus.DRAFT)
    methodology: Mapped[str] = mapped_column(String, default="BDN + tank soundings")
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Voyage(Base):
    """Raw voyage/fuel data — canonical shape shared by IMO DCS SEEMP Part II and EU MRV."""

    __tablename__ = "voyages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessels.id"))
    departure_port: Mapped[str] = mapped_column(String, nullable=False)
    arrival_port: Mapped[str] = mapped_column(String, nullable=False)
    departure_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    arrival_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    distance_nm: Mapped[float] = mapped_column(Float, nullable=False)
    fuel_type: Mapped[str] = mapped_column(String, default="VLSFO")
    fuel_consumed_mt: Mapped[float] = mapped_column(Float, nullable=False)
    intra_eu: Mapped[bool] = mapped_column(Boolean, default=False)  # 100% ETS exposure vs 50% extra-EU


class EmissionReportStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    DOC_ISSUED = "doc_issued"  # Document of Compliance issued


class EmissionReport(Base):
    """THETIS-MRV step 2-4: annual emission report -> verifier -> Document of Compliance."""

    __tablename__ = "emission_reports"
    __table_args__ = (UniqueConstraint("vessel_id", "year"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vessel_id: Mapped[int] = mapped_column(ForeignKey("vessels.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    total_co2_t: Mapped[float] = mapped_column(Float, nullable=False)
    ets_eligible_co2_t: Mapped[float] = mapped_column(Float, nullable=False)  # after intra/extra-EU weighting
    status: Mapped[EmissionReportStatus] = mapped_column(db_enum(EmissionReportStatus), default=EmissionReportStatus.DRAFT)


# --------------------------------------------------------------------------
# Module 3: CBAM — Transitional Registry 3-way split
# --------------------------------------------------------------------------
class CbamAuthStatus(str, enum.Enum):
    PENDING = "pending"
    AUTHORISED = "authorised"  # Authorisation Management Module
    SUSPENDED = "suspended"


class CbamDeclarant(Base):
    """Authorisation Management Module: importer/customs-rep authorised as CBAM declarant."""

    __tablename__ = "cbam_declarants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    eori_number: Mapped[str] = mapped_column(String, nullable=False)
    auth_status: Mapped[CbamAuthStatus] = mapped_column(db_enum(CbamAuthStatus), default=CbamAuthStatus.PENDING)


class CbamDefaultValue(Base):
    """Reference table: EU default embedded-emissions factors, versioned by regulation."""

    __tablename__ = "cbam_default_values"
    __table_args__ = (UniqueConstraint("cn_code", "country", "valid_from"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    cn_code: Mapped[str] = mapped_column(String, nullable=False)
    good_name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)  # "default" = rest-of-world fallback
    direct_emissions_factor: Mapped[float] = mapped_column(Float, nullable=False)  # tCO2e / tonne product
    indirect_emissions_factor: Mapped[float] = mapped_column(Float, default=0.0)
    markup_pct: Mapped[float] = mapped_column(Float, default=0.0)  # escalating 10/20/30% mark-up
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)


class EmissionSource(str, enum.Enum):
    DEFAULT_VALUE = "default_value"
    ACTUAL_VERIFIED = "actual_verified"


class CbamGoodsImport(Base):
    """Trader Portal: a single declared import consignment."""

    __tablename__ = "cbam_goods_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    declarant_id: Mapped[int] = mapped_column(ForeignKey("cbam_declarants.id"))
    cn_code: Mapped[str] = mapped_column(String, nullable=False)
    good_name: Mapped[str] = mapped_column(String, nullable=False)
    country_of_origin: Mapped[str] = mapped_column(String, nullable=False)
    quantity_t: Mapped[float] = mapped_column(Float, nullable=False)
    import_date: Mapped[date] = mapped_column(Date, nullable=False)
    emission_source: Mapped[EmissionSource] = mapped_column(db_enum(EmissionSource), default=EmissionSource.DEFAULT_VALUE)
    direct_emissions_t: Mapped[float] = mapped_column(Float, nullable=False)
    indirect_emissions_t: Mapped[float] = mapped_column(Float, default=0.0)


class CbamCertificateStatus(str, enum.Enum):
    HELD = "held"
    SURRENDERED = "surrendered"
    REPURCHASED = "repurchased"


class CbamCertificate(Base):
    __tablename__ = "cbam_certificates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    declarant_id: Mapped[int] = mapped_column(ForeignKey("cbam_declarants.id"))
    quantity_t_co2: Mapped[float] = mapped_column(Float, nullable=False)
    price_eur_per_t: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[CbamCertificateStatus] = mapped_column(db_enum(CbamCertificateStatus), default=CbamCertificateStatus.HELD)


class CbamDeclarationStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECONCILED = "reconciled"  # Data Reconciliation for Monitoring & Control


class CbamDeclaration(Base):
    """Data Reconciliation for Monitoring & Control: quarterly roll-up."""

    __tablename__ = "cbam_declarations"
    __table_args__ = (UniqueConstraint("declarant_id", "year", "quarter"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    declarant_id: Mapped[int] = mapped_column(ForeignKey("cbam_declarants.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    quarter: Mapped[int] = mapped_column(Integer, nullable=False)
    total_embedded_emissions_t: Mapped[float] = mapped_column(Float, nullable=False)
    certificates_surrendered_t: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[CbamDeclarationStatus] = mapped_column(db_enum(CbamDeclarationStatus), default=CbamDeclarationStatus.DRAFT)


class CbamPhaseInSchedule(Base):
    """CBAM's real regulatory phase-in (Reg. (EU) 2023/956 Art. 31(a), as amended by
    the Omnibus Regulation (EU) 2025/2083, 17 Oct 2025): free allocation to the
    equivalent EU ETS sector phases OUT 2026-2034, so the share of embedded emissions
    actually requiring a surrendered certificate (the 'CBAM factor') ramps from 2.5%
    in 2026 to 100% by 2034. This is NOT a supply-vs-demand gap in the EU ETS/CCTS
    sense — CBAM certificates aren't volume-capped; the EU sells as many as declarants
    need, priced weekly off the EUA auction average (Art. 21) — so there's no scarcity
    to model. The only real "gap" is temporal: the difference between what a declarant
    will eventually owe (100% basis) and what they actually owe today."""

    __tablename__ = "cbam_phase_in_schedule"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    year: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    free_allocation_pct: Mapped[float] = mapped_column(Float, nullable=False)
    cbam_factor_pct: Mapped[float] = mapped_column(Float, nullable=False)  # = 100 - free_allocation_pct
    note: Mapped[str | None] = mapped_column(String, nullable=True)


# --------------------------------------------------------------------------
# Module 4: Carbon credit sourcing/marketplace — CAD Trust hierarchy
# --------------------------------------------------------------------------
class CreditProgram(Base):
    __tablename__ = "credit_programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Verra, Gold Standard, ACR...


class CreditMethodology(Base):
    __tablename__ = "credit_methodologies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("credit_programs.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    sector: Mapped[str] = mapped_column(String, nullable=False)  # forestry, renewable energy, ...


class CreditProjectStatus(str, enum.Enum):
    PROPOSED = "proposed"
    REGISTERED = "registered"
    ISSUING = "issuing"
    SUSPENDED = "suspended"


class CreditProject(Base):
    __tablename__ = "credit_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    program_id: Mapped[int] = mapped_column(ForeignKey("credit_programs.id"))
    methodology_id: Mapped[int] = mapped_column(ForeignKey("credit_methodologies.id"))
    developer_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[CreditProjectStatus] = mapped_column(db_enum(CreditProjectStatus), default=CreditProjectStatus.REGISTERED)


class CreditIssuance(Base):
    __tablename__ = "credit_issuances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("credit_projects.id"))
    vintage_year: Mapped[int] = mapped_column(Integer, nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    issuance_date: Mapped[date] = mapped_column(Date, nullable=False)


class CreditUnitStatus(str, enum.Enum):
    STAGED = "staged"       # proposed, awaiting verification
    ISSUED = "issued"
    HELD = "held"
    RETIRED = "retired"
    TRANSFERRED = "transferred"


class CreditUnit(Base):
    """cadt-style staged-write unit: proposed -> verified -> committed (issued/held/retired)."""

    __tablename__ = "credit_units"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    issuance_id: Mapped[int] = mapped_column(ForeignKey("credit_issuances.id"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[CreditUnitStatus] = mapped_column(db_enum(CreditUnitStatus), default=CreditUnitStatus.STAGED)
    current_owner_org_id: Mapped[int | None] = mapped_column(ForeignKey("organizations.id"), nullable=True)


# --------------------------------------------------------------------------
# Module 5: Verification — cross-cutting stage/verify/commit workflow
# --------------------------------------------------------------------------
class VerificationSubjectType(str, enum.Enum):
    EMISSION_REPORT = "emission_report"
    CBAM_DECLARATION = "cbam_declaration"
    CREDIT_UNIT_BATCH = "credit_unit_batch"
    INSTALLATION_COMPLIANCE = "installation_compliance"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    VERIFIED = "verified"
    NON_CONFORMANCE = "non_conformance"


class VerificationRecord(Base):
    __tablename__ = "verification_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject_type: Mapped[VerificationSubjectType] = mapped_column(db_enum(VerificationSubjectType), nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    verifier_org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    status: Mapped[VerificationStatus] = mapped_column(db_enum(VerificationStatus), default=VerificationStatus.PENDING)
    findings: Mapped[str] = mapped_column(String, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


# --------------------------------------------------------------------------
# Module 6: Trading — one order book / position ledger for all instrument kinds
# --------------------------------------------------------------------------
class InstrumentType(str, enum.Enum):
    EUA = "EUA"
    EUAA = "EUAA"  # aviation allowances
    CBAM_CERTIFICATE = "CBAM_CERTIFICATE"
    VOLUNTARY_CREDIT = "VOLUNTARY_CREDIT"


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_type: Mapped[InstrumentType] = mapped_column(db_enum(InstrumentType), nullable=False)
    symbol: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    reference_credit_project_id: Mapped[int | None] = mapped_column(ForeignKey("credit_projects.id"), nullable=True)


class OrderSide(str, enum.Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(str, enum.Enum):
    OPEN = "open"
    FILLED = "filled"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    side: Mapped[OrderSide] = mapped_column(db_enum(OrderSide), nullable=False)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    limit_price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(db_enum(OrderStatus), default=OrderStatus.OPEN)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    buy_order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    sell_order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price_eur: Mapped[float] = mapped_column(Float, nullable=False)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class Position(Base):
    __tablename__ = "positions"
    __table_args__ = (UniqueConstraint("org_id", "instrument_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    org_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"))
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    quantity: Mapped[float] = mapped_column(Float, default=0.0)
    avg_cost_eur: Mapped[float] = mapped_column(Float, default=0.0)


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("instrument_id", "price_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"))
    price_date: Mapped[date] = mapped_column(Date, nullable=False)
    price_eur: Mapped[float] = mapped_column(Float, nullable=False)


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
