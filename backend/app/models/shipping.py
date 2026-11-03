"""Module 2: Shipping MRV."""
from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import db_enum
from .tenancy import Organization


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
