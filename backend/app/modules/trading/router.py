from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/trading", tags=["Trading"])


@router.get("/instruments", response_model=list[schemas.InstrumentOut])
def list_instruments(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return db.query(models.Instrument).all()


@router.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(status: str | None = None, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    """The open order book is public market data, like a real exchange — visible cross-tenant."""
    q = db.query(models.Order)
    if status:
        q = q.filter(models.Order.status == status)
    return q.order_by(models.Order.created_at.desc()).all()


@router.get("/trades", response_model=list[schemas.TradeOut])
def list_trades(
    instrument_id: int | None = None, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    q = db.query(models.Trade)
    if instrument_id:
        q = q.filter(models.Trade.instrument_id == instrument_id)
    return q.order_by(models.Trade.executed_at.desc()).all()


@router.get("/positions", response_model=list[schemas.PositionOut])
def list_positions(
    org_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """Positions are private — always scoped to the caller's tenant, regardless of org_id passed."""
    my_org_ids = get_my_org_ids(db, user.tenant_id)
    q = db.query(models.Position).filter(models.Position.org_id.in_(my_org_ids))
    if org_id:
        if org_id not in my_org_ids:
            raise HTTPException(403, "org_id does not belong to your tenant")
        q = q.filter(models.Position.org_id == org_id)
    return q.all()


@router.get("/prices/{instrument_id}", response_model=list[schemas.PriceHistoryOut])
def price_history(instrument_id: int, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return (
        db.query(models.PriceHistory)
        .filter_by(instrument_id=instrument_id)
        .order_by(models.PriceHistory.price_date)
        .all()
    )


def _apply_fill(db: Session, org_id: int, instrument_id: int, side: models.OrderSide, qty: float, price: float):
    pos = db.query(models.Position).filter_by(org_id=org_id, instrument_id=instrument_id).first()
    if pos is None:
        pos = models.Position(org_id=org_id, instrument_id=instrument_id, quantity=0.0, avg_cost_eur=0.0)
        db.add(pos)
        db.flush()

    if side == models.OrderSide.BUY:
        new_qty = pos.quantity + qty
        if new_qty > 0:
            pos.avg_cost_eur = ((pos.avg_cost_eur * pos.quantity) + (price * qty)) / new_qty
        pos.quantity = new_qty
    else:
        pos.quantity -= qty


@router.post("/orders", response_model=schemas.OrderOut)
def place_order(req: schemas.OrderCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Simple price-time-priority matching against resting opposite-side orders
    on the same instrument, then rests any unfilled remainder."""
    org = db.get(models.Organization, req.org_id)
    if org is None or org.tenant_id != user.tenant_id:
        raise HTTPException(403, "org_id does not belong to your tenant")

    side = models.OrderSide(req.side)
    if side == models.OrderSide.BUY:
        opposite = models.OrderSide.SELL
        price_ok = lambda resting: resting.limit_price_eur <= req.limit_price_eur
    else:
        opposite = models.OrderSide.BUY
        price_ok = lambda resting: resting.limit_price_eur >= req.limit_price_eur

    order = models.Order(
        org_id=req.org_id,
        instrument_id=req.instrument_id,
        side=side,
        quantity=req.quantity,
        limit_price_eur=req.limit_price_eur,
        status=models.OrderStatus.OPEN,
    )
    db.add(order)
    db.flush()

    remaining = req.quantity
    resting_orders = (
        db.query(models.Order)
        .filter_by(instrument_id=req.instrument_id, side=opposite, status=models.OrderStatus.OPEN)
        .order_by(models.Order.created_at.asc())
        .all()
    )
    for resting in resting_orders:
        if remaining <= 0:
            break
        if not price_ok(resting):
            continue
        fill_qty = min(remaining, resting.quantity)
        fill_price = resting.limit_price_eur  # resting order sets the price
        buy_order_id = order.id if side == models.OrderSide.BUY else resting.id
        sell_order_id = resting.id if side == models.OrderSide.BUY else order.id

        db.add(
            models.Trade(
                buy_order_id=buy_order_id,
                sell_order_id=sell_order_id,
                instrument_id=req.instrument_id,
                quantity=fill_qty,
                price_eur=fill_price,
            )
        )
        _apply_fill(db, order.org_id, req.instrument_id, side, fill_qty, fill_price)
        _apply_fill(db, resting.org_id, req.instrument_id, opposite, fill_qty, fill_price)

        resting.quantity -= fill_qty
        remaining -= fill_qty
        if resting.quantity <= 0:
            resting.status = models.OrderStatus.FILLED

    order.quantity = remaining  # remaining OPEN quantity; executed size is on the Trade rows
    order.status = models.OrderStatus.FILLED if remaining <= 0 else models.OrderStatus.OPEN

    db.commit()
    db.refresh(order)
    return order


@router.delete("/orders/{order_id}")
def cancel_order(order_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    order = db.query(models.Order).get(order_id)
    if order is None:
        raise HTTPException(404, "Order not found")
    org = db.get(models.Organization, order.org_id)
    if org is None or org.tenant_id != user.tenant_id:
        raise HTTPException(403, "This order does not belong to your tenant")
    if order.status != models.OrderStatus.OPEN:
        raise HTTPException(400, "Only open orders can be cancelled")
    order.status = models.OrderStatus.CANCELLED
    db.commit()
    return {"ok": True}
