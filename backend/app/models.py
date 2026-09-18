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
    name: Mapped[str] = mapped_column(String, nullable=False)
    org_type: Mapped[OrgType] = mapped_column(db_enum(OrgType), nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=True)
    lei_or_eori: Mapped[str] = mapped_column(String, nullable=True)


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
