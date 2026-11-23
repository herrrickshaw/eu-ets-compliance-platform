"""Unit tests for the pure service functions extracted from the routers."""
from __future__ import annotations

from types import SimpleNamespace as NS

import pytest
from app import models
from app.modules.cbam import service as cbam
from app.modules.india_ccts import service as india
from app.modules.shipping_mrv import service as ship
from app.modules.trading import service as trading

BUY, SELL = models.OrderSide.BUY, models.OrderSide.SELL


def test_voyage_summary_weights_intra_eu_fully():
    total, ets = ship.summarise_voyages([NS(fuel_consumed_mt=10, intra_eu=True), NS(fuel_consumed_mt=20, intra_eu=False)])
    assert total == pytest.approx(30 * 3.114)
    assert ets == pytest.approx(10 * 3.114 + 20 * 3.114 * 0.5)


def test_quarter_window_rolls_year_in_q4():
    assert cbam.quarter_window(2026, 1) == ("2026-01-01", "2026-04-01")
    assert cbam.quarter_window(2026, 4) == ("2026-10-01", "2027-01-01")


def test_marked_up_emissions_applies_markup():
    dv = NS(direct_emissions_factor=2.0, indirect_emissions_factor=1.0, markup_pct=10.0)
    assert cbam.marked_up_emissions(dv, 100) == (220.0, 110.0)


def test_surrender_marks_only_fully_used_certificates():
    certs = [NS(quantity_t_co2=10.0, status=None), NS(quantity_t_co2=10.0, status=None)]
    assert cbam.surrender_held_certificates(certs, 15.0) == 15.0
    assert certs[0].status == models.CbamCertificateStatus.SURRENDERED
    assert certs[1].status is None
    assert cbam.surrender_held_certificates([NS(quantity_t_co2=5.0, status=None)], 50.0) == 5.0


def test_crosses_by_side():
    assert trading.crosses(BUY, 70.0, 71.0) and not trading.crosses(BUY, 72.0, 71.0)
    assert trading.crosses(SELL, 70.0, 69.0) and not trading.crosses(SELL, 70.0, 71.0)


def test_plan_fills_partial_fill_and_remainder():
    book = [NS(quantity=60.0, limit_price_eur=70.0), NS(quantity=60.0, limit_price_eur=75.0), NS(quantity=10.0, limit_price_eur=71.0)]
    fills, remaining = trading.plan_fills(BUY, 100.0, 72.0, book)
    assert [(f.quantity, f.price_eur) for f in fills] == [(60.0, 70.0), (10.0, 71.0)]
    assert remaining == 30.0
    assert book[0].quantity == 60.0  # planning does not mutate


def test_apply_fill_to_position_weighted_average_cost():
    pos = NS(quantity=10.0, avg_cost_eur=60.0)
    trading.apply_fill_to_position(pos, BUY, 10.0, 80.0)
    assert (pos.quantity, pos.avg_cost_eur) == (20.0, 70.0)
    trading.apply_fill_to_position(pos, SELL, 5.0, 99.0)
    assert (pos.quantity, pos.avg_cost_eur) == (15.0, 70.0)


def test_estimate_capacity_credits_handles_missing_figures():
    b = NS(mwh_per_mw_per_year=2000.0, tco2e_per_mw_per_year=None)
    assert india.estimate_capacity_credits(b, 1.2345) == (2469.0, None)


def test_split_supply_separates_figure_types():
    rows = [
        NS(potential_avoided_mt_co2e=None, metric_label="m", source_name="s", figure_type=None),
        NS(potential_avoided_mt_co2e=5.0, metric_label="a", source_name="s", figure_type=models.FigureType.ASPIRATIONAL_TARGET),
        NS(potential_avoided_mt_co2e=2.0, metric_label="b", source_name="s", figure_type=models.FigureType.AWARDED_OPERATIONAL),
    ]
    assert india.split_supply(rows) == (2.0, 5.0, ["m (s)"])
