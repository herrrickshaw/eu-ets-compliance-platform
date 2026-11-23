from datetime import datetime, timedelta

import pytest

from app import models

BUY, SELL = models.OrderSide.BUY, models.OrderSide.SELL
T0 = datetime(2030, 1, 1)


@pytest.fixture
def inst(make):
    return make.add(models.Instrument(instrument_type=models.InstrumentType.EUA, symbol="EUA-T"))


def rest(make, org, inst, side, qty, price, age=0):
    """Insert a resting OPEN order directly. ``age`` orders time priority (higher = older)."""
    return make.add(
        models.Order(
            org_id=org.id,
            instrument_id=inst.id,
            side=side,
            quantity=qty,
            limit_price_eur=price,
            status=models.OrderStatus.OPEN,
            created_at=T0 - timedelta(minutes=age),
        )
    )


def place(client, headers, org, inst, side, qty, price):
    return client.post(
        "/api/trading/orders",
        json={"org_id": org.id, "instrument_id": inst.id, "side": side, "quantity": qty, "limit_price_eur": price},
        headers=headers,
    )


def pos(db, org, inst):
    db.expire_all()
    return db.query(models.Position).filter_by(org_id=org.id, instrument_id=inst.id).first()


def test_order_with_no_counterparty_rests_open(client, two_tenants, inst, db):
    (_, _, oa, ha), _ = two_tenants
    r = place(client, ha, oa, inst, "buy", 10, 50)
    assert r.status_code == 200
    assert (r.json()["status"], r.json()["quantity"]) == ("open", 10)
    assert db.query(models.Trade).count() == 0
    assert pos(db, oa, inst) is None


def test_full_match_executes_at_resting_price(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    resting = rest(make, ob, inst, SELL, 10, 90)
    r = place(client, ha, oa, inst, "buy", 10, 100)
    assert r.json()["status"] == "filled"
    assert r.json()["quantity"] == 0
    t = db.query(models.Trade).one()
    assert (t.price_eur, t.quantity) == (90, 10)  # resting price, not the aggressor's limit
    assert t.sell_order_id == resting.id
    assert pos(db, oa, inst).quantity == 10
    assert pos(db, oa, inst).avg_cost_eur == 90
    assert pos(db, ob, inst).quantity == -10
    db.expire_all()
    assert db.get(models.Order, resting.id).status == models.OrderStatus.FILLED


def test_partial_fill_leaves_remainder_open(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    resting = rest(make, ob, inst, SELL, 4, 90)
    r = place(client, ha, oa, inst, "buy", 10, 100)
    assert (r.json()["status"], r.json()["quantity"]) == ("open", 6)
    assert db.query(models.Trade).one().quantity == 4
    db.expire_all()
    assert db.get(models.Order, resting.id).status == models.OrderStatus.FILLED


def test_aggressor_smaller_than_resting_reduces_resting_quantity(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    resting = rest(make, ob, inst, SELL, 10, 90)
    place(client, ha, oa, inst, "buy", 3, 100)
    db.expire_all()
    r = db.get(models.Order, resting.id)
    assert (r.quantity, r.status) == (7, models.OrderStatus.OPEN)


def test_price_boundary_buy_equal_price_matches_one_cent_higher_does_not(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    rest(make, ob, inst, SELL, 5, 100.0)
    no = place(client, ha, oa, inst, "buy", 5, 99.99)
    assert no.json()["status"] == "open"
    assert db.query(models.Trade).count() == 0
    yes = place(client, ha, oa, inst, "buy", 5, 100.0)
    assert yes.json()["status"] == "filled"
    assert db.query(models.Trade).count() == 1


def test_sell_matches_resting_buy_at_or_above_limit(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    rest(make, ob, inst, BUY, 5, 80.0)
    assert place(client, ha, oa, inst, "sell", 5, 80.01).json()["status"] == "open"
    assert db.query(models.Trade).count() == 0
    r = place(client, ha, oa, inst, "sell", 5, 80.0)
    assert r.json()["status"] == "filled"
    t = db.query(models.Trade).one()
    assert t.price_eur == 80.0
    assert t.buy_order_id != t.sell_order_id
    assert pos(db, ob, inst).quantity == 5
    assert pos(db, oa, inst).quantity == -5


def test_time_priority_oldest_resting_first_and_skips_unacceptable_prices(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    newer = rest(make, ob, inst, SELL, 5, 90, age=1)
    older = rest(make, ob, inst, SELL, 5, 95, age=10)
    too_dear = rest(make, ob, inst, SELL, 5, 200, age=20)
    place(client, ha, oa, inst, "buy", 7, 100)
    trades = db.query(models.Trade).order_by(models.Trade.id).all()
    assert [(t.sell_order_id, t.quantity, t.price_eur) for t in trades] == [
        (older.id, 5, 95),
        (newer.id, 2, 90),
    ]
    db.expire_all()
    assert db.get(models.Order, too_dear.id).quantity == 5
    assert db.get(models.Order, too_dear.id).status == models.OrderStatus.OPEN


def test_average_cost_is_quantity_weighted(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    rest(make, ob, inst, SELL, 10, 80, age=2)
    rest(make, ob, inst, SELL, 10, 100, age=1)
    place(client, ha, oa, inst, "buy", 20, 120)
    p = pos(db, oa, inst)
    assert p.quantity == 20
    assert p.avg_cost_eur == pytest.approx(90.0)


def test_does_not_match_other_instrument_or_same_side(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    other = make.add(models.Instrument(instrument_type=models.InstrumentType.EUAA, symbol="EUAA-T"))
    rest(make, ob, other, SELL, 5, 10)
    rest(make, ob, inst, BUY, 5, 10)
    r = place(client, ha, oa, inst, "buy", 5, 1000)
    assert r.json()["status"] == "open"
    assert db.query(models.Trade).count() == 0


def test_order_for_other_tenants_org_forbidden(client, two_tenants, inst, db):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    assert place(client, ha, ob, inst, "buy", 1, 1).status_code == 403
    assert db.query(models.Order).count() == 0


def test_cancel_order(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    o = rest(make, oa, inst, BUY, 5, 10)
    assert client.delete(f"/api/trading/orders/{o.id}", headers=hb).status_code == 403
    assert client.delete("/api/trading/orders/9999", headers=ha).status_code == 404
    assert client.delete(f"/api/trading/orders/{o.id}", headers=ha).json() == {"ok": True}
    db.expire_all()
    assert db.get(models.Order, o.id).status == models.OrderStatus.CANCELLED
    again = client.delete(f"/api/trading/orders/{o.id}", headers=ha)
    assert (again.status_code, again.json()["detail"]) == (400, "Only open orders can be cancelled")


def test_orders_listing_newest_first_with_status_filter(client, make, two_tenants, inst):
    (_, _, oa, ha), _ = two_tenants
    old = rest(make, oa, inst, BUY, 1, 1, age=10)
    new = rest(make, oa, inst, BUY, 1, 1, age=1)
    filled = rest(make, oa, inst, BUY, 1, 1, age=5)
    filled.status = models.OrderStatus.FILLED
    make.db.commit()
    ids = [o["id"] for o in client.get("/api/trading/orders", headers=ha).json()]
    assert ids == [new.id, filled.id, old.id]
    only_open = [o["id"] for o in client.get("/api/trading/orders?status=open", headers=ha).json()]
    assert only_open == [new.id, old.id]


def test_trades_filter_and_order(client, make, two_tenants, inst):
    (_, _, oa, ha), _ = two_tenants
    other = make.add(models.Instrument(instrument_type=models.InstrumentType.EUAA, symbol="EUAA-T"))
    b = rest(make, oa, inst, BUY, 1, 1)
    s = rest(make, oa, inst, SELL, 1, 1)
    early = make.add(models.Trade(buy_order_id=b.id, sell_order_id=s.id, instrument_id=inst.id, quantity=1, price_eur=1, executed_at=T0))
    late = make.add(models.Trade(buy_order_id=b.id, sell_order_id=s.id, instrument_id=inst.id, quantity=1, price_eur=1, executed_at=T0 + timedelta(days=1)))
    make.add(models.Trade(buy_order_id=b.id, sell_order_id=s.id, instrument_id=other.id, quantity=1, price_eur=1, executed_at=T0))
    all_ids = [t["id"] for t in client.get("/api/trading/trades", headers=ha).json()]
    assert len(all_ids) == 3 and all_ids[0] == late.id
    filtered = [t["id"] for t in client.get(f"/api/trading/trades?instrument_id={inst.id}", headers=ha).json()]
    assert filtered == [late.id, early.id]


def test_positions_are_private_to_tenant(client, make, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, hb) = two_tenants
    make.add(models.Position(org_id=oa.id, instrument_id=inst.id, quantity=5))
    make.add(models.Position(org_id=ob.id, instrument_id=inst.id, quantity=9))
    assert [p["quantity"] for p in client.get("/api/trading/positions", headers=ha).json()] == [5]
    assert [p["quantity"] for p in client.get(f"/api/trading/positions?org_id={oa.id}", headers=ha).json()] == [5]
    r = client.get(f"/api/trading/positions?org_id={ob.id}", headers=ha)
    assert r.status_code == 403


def test_price_history_sorted_by_date(client, make, two_tenants, inst):
    (_, _, _, ha), _ = two_tenants
    from datetime import date

    for d, p in [(date(2030, 1, 3), 3.0), (date(2030, 1, 1), 1.0), (date(2030, 1, 2), 2.0)]:
        make.add(models.PriceHistory(instrument_id=inst.id, price_date=d, price_eur=p))
    prices = [x["price_eur"] for x in client.get(f"/api/trading/prices/{inst.id}", headers=ha).json()]
    assert prices == [1.0, 2.0, 3.0]
    assert client.get("/api/trading/prices/9999", headers=ha).json() == []


def test_instruments_and_market_reality(client, make, two_tenants, inst):
    (_, _, _, ha), _ = two_tenants
    assert [i["symbol"] for i in client.get("/api/trading/instruments", headers=ha).json()] == ["EUA-T"]
    common = dict(period="p", unit="u", source_name="s", source_confidence=models.SourceConfidence.SECONDARY)
    make.add(models.EuaTradingMarketStat(category="b", metric_label="b1", **common))
    make.add(models.EuaTradingMarketStat(category="a", metric_label="a1", **common))
    assert [s["metric_label"] for s in client.get("/api/trading/market-reality", headers=ha).json()] == ["a1", "b1"]


@pytest.mark.xfail(strict=True, raises=ValueError, reason="place_order does models.OrderSide(req.side) on an unvalidated string: side='hold' raises ValueError (HTTP 500) instead of a 4xx validation error")
def test_invalid_side_should_be_a_client_error(client, two_tenants, inst):
    (_, _, oa, ha), _ = two_tenants
    r = place(client, ha, oa, inst, "hold", 1, 1)
    assert 400 <= r.status_code < 500


def test_matching_stops_once_order_is_filled(client, make, db, two_tenants, inst):
    (_, _, oa, ha), (_, _, ob, _) = two_tenants
    first = rest(make, ob, inst, SELL, 5, 90, age=3)
    second = rest(make, ob, inst, SELL, 5, 91, age=2)
    place(client, ha, oa, inst, "buy", 5, 100)
    assert [t.sell_order_id for t in db.query(models.Trade).all()] == [first.id]
    db.expire_all()
    assert db.get(models.Order, second.id).quantity == 5
    assert db.get(models.Order, second.id).status == models.OrderStatus.OPEN
