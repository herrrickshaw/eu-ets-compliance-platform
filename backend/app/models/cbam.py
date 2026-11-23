"""Module 3: CBAM."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base
from .base import db_enum


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
