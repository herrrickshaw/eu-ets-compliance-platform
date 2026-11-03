"""Module 6: Trading."""
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
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base
from .base import _now, db_enum


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
