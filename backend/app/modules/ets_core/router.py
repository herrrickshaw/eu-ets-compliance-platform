from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/ets", tags=["EU ETS core"])


@router.get("/installations", response_model=list[schemas.InstallationOut])
def list_installations(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    return db.query(models.Installation).filter(models.Installation.org_id.in_(org_ids)).all()


@router.get("/accounts", response_model=list[schemas.AllowanceAccountOut])
def list_accounts(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    return db.query(models.AllowanceAccount).filter(models.AllowanceAccount.org_id.in_(org_ids)).all()


@router.get("/compliance", response_model=list[schemas.ComplianceStatusOut])
def list_compliance(
    year: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.ComplianceStatus)
        .join(models.Installation, models.ComplianceStatus.installation_id == models.Installation.id)
        .filter(models.Installation.org_id.in_(org_ids))
    )
    if year:
        q = q.filter(models.ComplianceStatus.year == year)
    return q.all()


@router.post("/surrender", response_model=schemas.ComplianceStatusOut)
def surrender_allowances(
    req: schemas.SurrenderRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    installation = db.get(models.Installation, req.installation_id)
    if installation is None:
        raise HTTPException(404, "Installation not found")
    org = db.get(models.Organization, installation.org_id)
    if org is None or org.tenant_id != user.tenant_id:
        raise HTTPException(403, "This installation does not belong to your tenant")

    status_row = (
        db.query(models.ComplianceStatus)
        .filter_by(installation_id=req.installation_id, year=req.year)
        .first()
    )
    if not status_row:
        raise HTTPException(404, "No compliance record for that installation/year")

    account = (
        db.query(models.AllowanceAccount)
        .filter_by(installation_id=req.installation_id, account_type=models.AccountType.OPERATOR_HOLDING)
        .first()
    )
    if not account:
        raise HTTPException(404, "No operator holding account for this installation")
    if account.balance < req.amount_t:
        raise HTTPException(400, f"Insufficient EUA balance: has {account.balance}, needs {req.amount_t}")

    account.balance -= req.amount_t
    status_row.allowances_surrendered_t += req.amount_t
    db.add(
        models.AllowanceTransaction(
            account_id=account.id,
            txn_type=models.AllowanceTxnType.SURRENDER,
            amount=req.amount_t,
            compliance_year=req.year,
        )
    )

    shortfall = status_row.verified_emissions_t - status_row.allowances_surrendered_t
    if shortfall <= 0:
        status_row.status = "compliant"
    elif status_row.surrender_deadline < date.today():
        status_row.status = "penalized"
    else:
        status_row.status = "short"

    db.commit()
    db.refresh(status_row)
    return status_row


@router.get("/system-stats", response_model=list[schemas.EtsCoreSystemStatOut])
def list_system_stats(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return (
        db.query(models.EtsCoreSystemStat)
        .order_by(models.EtsCoreSystemStat.category, models.EtsCoreSystemStat.id)
        .all()
    )
