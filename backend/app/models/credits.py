"""Module 4: Carbon credit sourcing/marketplace."""
from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import (
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base
from .base import db_enum


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
