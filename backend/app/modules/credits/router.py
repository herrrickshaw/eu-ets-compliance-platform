from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user
from ...db import get_db

router = APIRouter(prefix="/api/credits", tags=["Carbon credit sourcing"])


@router.get("/projects", response_model=list[schemas.CreditProjectOut])
def list_projects(
    country: str | None = None, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    """Registered projects are marketplace listings, visible cross-tenant (like a real credit registry)."""
    q = db.query(models.CreditProject)
    if country:
        q = q.filter(models.CreditProject.country == country)
    return q.all()


@router.get("/units", response_model=list[schemas.CreditUnitOut])
def list_units(
    status: str | None = None, db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)
):
    q = db.query(models.CreditUnit)
    if status:
        q = q.filter(models.CreditUnit.status == status)
    return q.all()


@router.post("/units/{unit_id}/purchase", response_model=schemas.CreditUnitOut)
def purchase_unit(
    unit_id: int,
    req: schemas.CreditPurchaseRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """cadt-style commit step: a unit already ISSUED (past verification) transfers ownership."""
    buyer_org = db.get(models.Organization, req.buyer_org_id)
    if buyer_org is None or buyer_org.tenant_id != user.tenant_id:
        raise HTTPException(403, "buyer_org_id does not belong to your tenant")

    unit = db.query(models.CreditUnit).get(unit_id)
    if unit is None:
        raise HTTPException(404, "Unit not found")
    if unit.status not in (models.CreditUnitStatus.ISSUED, models.CreditUnitStatus.HELD):
        raise HTTPException(400, f"Unit is {unit.status.value}, not available for purchase")
    unit.current_owner_org_id = req.buyer_org_id
    unit.status = models.CreditUnitStatus.HELD
    db.commit()
    db.refresh(unit)
    return unit


@router.post("/units/{unit_id}/retire", response_model=schemas.CreditUnitOut)
def retire_unit(unit_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    unit = db.query(models.CreditUnit).get(unit_id)
    if unit is None:
        raise HTTPException(404, "Unit not found")
    owner_org = db.get(models.Organization, unit.current_owner_org_id) if unit.current_owner_org_id else None
    if owner_org is None or owner_org.tenant_id != user.tenant_id:
        raise HTTPException(403, "You do not own this unit")
    if unit.status != models.CreditUnitStatus.HELD:
        raise HTTPException(400, "Only held units can be retired")
    unit.status = models.CreditUnitStatus.RETIRED
    db.commit()
    db.refresh(unit)
    return unit
