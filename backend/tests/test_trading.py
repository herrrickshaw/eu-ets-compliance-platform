"""Order-book matching in app/modules/trading/router.py::place_order."""
from datetime import datetime

from app import models


def rest(db, org, inst, side, qty, px, t):
    o = models.Order(org_id=org.id, instrument_id=inst.id, side=side, quantity=qty, limit_price_eur=px,
                     status=models.OrderStatus.OPEN, created_at=t)
    db.add(o)
    db.commit()
    return o


def place(client, headers, org, inst, side, qty, px):
    return client.post("/api/trading/orders", headers=headers,
                       json={"org_id": org.id, "instrument_id": inst.id, "side": side,
                             "quantity": qty, "limit_price_eur": px})


def trades(db):
    return db.query(models.Trade).order_by(models.Trade.id).all()


def test_buy_matches_best_priced_ask_first_not_oldest(db, client, tenant, eua):
    """Price-time priority: a buy at 90 must lift the 70 ask before the older 80 ask."""
    seller, _ = tenant("seller")
    buyer, h = tenant("buyer")
    rest(db, seller, eua, models.OrderSide.SELL, 10, 80.0, datetime(2026, 1, 1, 9))
    best = rest(db, seller, eua, models.OrderSide.SELL, 10, 70.0, datetime(2026, 1, 1, 10))
    r = place(client, h, buyer, eua, "buy", 10, 90.0)
    assert r.status_code == 200
    t = trades(db)
    assert len(t) == 1
    assert t[0].price_eur == 70.0
    assert t[0].sell_order_id == best.id


def test_sell_matches_highest_bid_first(db, client, tenant, eua):
    bidder, _ = tenant("bidder")
    seller, h = tenant("seller")
    rest(db, bidder, eua, models.OrderSide.BUY, 5, 60.0, datetime(2026, 1, 1, 9))
    rest(db, bidder, eua, models.OrderSide.BUY, 5, 65.0, datetime(2026, 1, 1, 10))
    place(client, h, seller, eua, "sell", 5, 55.0)
    assert [t.price_eur for t in trades(db)] == [65.0]


def test_time_priority_breaks_ties_at_same_price(db, client, tenant, eua):
    s, _ = tenant("s")
    b, h = tenant("b")
    first = rest(db, s, eua, models.OrderSide.SELL, 4, 70.0, datetime(2026, 1, 1, 9))
    rest(db, s, eua, models.OrderSide.SELL, 4, 70.0, datetime(2026, 1, 1, 10))
    place(client, h, b, eua, "buy", 4, 70.0)
    assert [t.sell_order_id for t in trades(db)] == [first.id]


def test_sweep_across_levels_partial_fill_and_rest(db, client, tenant, eua):
    s, _ = tenant("s")
    b, h = tenant("b")
    a1 = rest(db, s, eua, models.OrderSide.SELL, 3, 71.0, datetime(2026, 1, 1, 9))
    a2 = rest(db, s, eua, models.OrderSide.SELL, 5, 72.0, datetime(2026, 1, 1, 8))
    rest(db, s, eua, models.OrderSide.SELL, 5, 80.0, datetime(2026, 1, 1, 7))  # above limit
    r = place(client, h, b, eua, "buy", 10, 75.0).json()
    assert [(t.sell_order_id, t.quantity, t.price_eur) for t in trades(db)] == [(a1.id, 3, 71.0), (a2.id, 5, 72.0)]
    assert r["status"] == "open" and r["quantity"] == 2  # remainder rests
    db.expire_all()
    assert db.get(models.Order, a1.id).status == models.OrderStatus.FILLED
    pos = db.query(models.Position).filter_by(org_id=b.id).one()
    assert pos.quantity == 8
    assert abs(pos.avg_cost_eur - (3 * 71 + 5 * 72) / 8) < 1e-9
    spos = db.query(models.Position).filter_by(org_id=s.id).one()
    assert spos.quantity == -8


def test_non_crossing_order_rests_without_trades(db, client, tenant, eua):
    s, _ = tenant("s")
    b, h = tenant("b")
    rest(db, s, eua, models.OrderSide.SELL, 3, 71.0, datetime(2026, 1, 1, 9))
    r = place(client, h, b, eua, "buy", 3, 70.0).json()
    assert trades(db) == [] and r["status"] == "open" and r["quantity"] == 3


def test_cannot_place_order_for_another_tenants_org(client, tenant, eua):
    other, _ = tenant("other")
    _, h = tenant("me")
    assert place(client, h, other, eua, "buy", 1, 70.0).status_code == 403


def test_rejects_non_positive_quantity_and_price(client, tenant, eua):
    org, h = tenant("me")
    assert place(client, h, org, eua, "buy", -5, 70.0).status_code == 422
    assert place(client, h, org, eua, "buy", 0, 70.0).status_code == 422
    assert place(client, h, org, eua, "sell", 5, -1.0).status_code == 422


def test_positions_are_tenant_scoped(db, client, tenant, eua):
    a, ha = tenant("a")
    b, hb = tenant("b")
    db.add(models.Position(org_id=a.id, instrument_id=eua.id, quantity=5, avg_cost_eur=70))
    db.commit()
    assert len(client.get("/api/trading/positions", headers=ha).json()) == 1
    assert client.get("/api/trading/positions", headers=hb).json() == []
    assert client.get(f"/api/trading/positions?org_id={a.id}", headers=hb).status_code == 403


def test_cancel_order_rules(db, client, tenant, eua):
    a, ha = tenant("a")
    _, hb = tenant("b")
    o = rest(db, a, eua, models.OrderSide.BUY, 1, 50.0, datetime(2026, 1, 1))
    assert client.delete(f"/api/trading/orders/{o.id}", headers=hb).status_code == 403
    assert client.delete(f"/api/trading/orders/{o.id}", headers=ha).status_code == 200
    assert client.delete(f"/api/trading/orders/{o.id}", headers=ha).status_code == 400
    assert client.delete("/api/trading/orders/9999", headers=ha).status_code == 404
