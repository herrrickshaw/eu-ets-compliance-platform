"""Order-matching and position arithmetic for the trading module (no DB access)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

from ... import models


@dataclass
class Fill:
    """One execution against a resting order; the resting order sets the price (EUR per unit)."""

    resting: Any
    quantity: float
    price_eur: float


def crosses(side: models.OrderSide, resting_price_eur: float, limit_price_eur: float) -> bool:
    """True if an incoming order on `side` at `limit_price_eur` can trade with the resting price."""
    if side == models.OrderSide.BUY:
        return resting_price_eur <= limit_price_eur
    return resting_price_eur >= limit_price_eur


def plan_fills(
    side: models.OrderSide, quantity: float, limit_price_eur: float, resting_orders: Iterable[Any]
) -> tuple[list[Fill], float]:
    """Price-time-priority matching over `resting_orders` (already time-sorted, opposite side).

    Returns (fills, unfilled remainder). Does not mutate the resting orders.
    """
    fills: list[Fill] = []
    remaining = quantity
    for resting in resting_orders:
        if remaining <= 0:
            break
        if not crosses(side, resting.limit_price_eur, limit_price_eur):
            continue
        fill_qty = min(remaining, resting.quantity)
        fills.append(Fill(resting=resting, quantity=fill_qty, price_eur=resting.limit_price_eur))
        remaining -= fill_qty
    return fills, remaining


def apply_fill_to_position(pos: Any, side: models.OrderSide, qty: float, price: float) -> None:
    """Update a position's quantity and (on buys) volume-weighted average cost in place."""
    if side == models.OrderSide.BUY:
        new_qty = pos.quantity + qty
        if new_qty > 0:
            pos.avg_cost_eur = ((pos.avg_cost_eur * pos.quantity) + (price * qty)) / new_qty
        pos.quantity = new_qty
    else:
        pos.quantity -= qty
