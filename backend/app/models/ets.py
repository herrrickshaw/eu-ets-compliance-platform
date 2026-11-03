"""Module 1: EU ETS core (installations, allowances)."""
from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base
from .base import _now, db_enum
from .tenancy import Organization


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
