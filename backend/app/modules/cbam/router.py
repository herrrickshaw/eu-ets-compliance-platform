from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/cbam", tags=["CBAM"])


def _require_declarant_in_tenant(db: Session, declarant_id: int, tenant_id: int) -> models.CbamDeclarant:
    declarant = db.get(models.CbamDeclarant, declarant_id)
    if declarant is None:
        raise HTTPException(404, "Declarant not found")
    org = db.get(models.Organization, declarant.org_id)
    if org is None or org.tenant_id != tenant_id:
        raise HTTPException(403, "This declarant does not belong to your tenant")
    return declarant


@router.get("/declarants", response_model=list[schemas.CbamDeclarantOut])
def list_declarants(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    org_ids = get_my_org_ids(db, user.tenant_id)
    return db.query(models.CbamDeclarant).filter(models.CbamDeclarant.org_id.in_(org_ids)).all()


@router.get("/default-values", response_model=list[schemas.CbamDefaultValueOut])
def list_default_values(cn_code: str | None = None, db: Session = Depends(get_db)):
    q = db.query(models.CbamDefaultValue)
    if cn_code:
        q = q.filter(models.CbamDefaultValue.cn_code == cn_code)
    return q.all()


@router.get("/imports", response_model=list[schemas.CbamGoodsImportOut])
def list_imports(
    declarant_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.CbamGoodsImport)
        .join(models.CbamDeclarant, models.CbamGoodsImport.declarant_id == models.CbamDeclarant.id)
        .filter(models.CbamDeclarant.org_id.in_(org_ids))
    )
    if declarant_id:
        q = q.filter(models.CbamGoodsImport.declarant_id == declarant_id)
    return q.all()


@router.post("/imports", response_model=schemas.CbamGoodsImportOut)
def create_import(
    req: schemas.CbamGoodsImportCreate, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """Trader Portal: declare an import consignment. Falls back to the EU default-value
    table (with its escalating mark-up) unless actual verified emissions are supplied —
    mirrors the CBAM Transitional Registry's 50%-default-value ceiling rule."""
    _require_declarant_in_tenant(db, req.declarant_id, user.tenant_id)

    if req.actual_direct_emissions_t is not None:
        direct_t = req.actual_direct_emissions_t
        indirect_t = req.actual_indirect_emissions_t or 0.0
        source = models.EmissionSource.ACTUAL_VERIFIED
    else:
        dv = (
            db.query(models.CbamDefaultValue)
            .filter_by(cn_code=req.cn_code, country=req.country_of_origin)
            .order_by(models.CbamDefaultValue.valid_from.desc())
            .first()
        )
        if dv is None:
            dv = (
                db.query(models.CbamDefaultValue)
                .filter_by(cn_code=req.cn_code, country="default")
                .order_by(models.CbamDefaultValue.valid_from.desc())
                .first()
            )
        if dv is None:
            raise HTTPException(404, f"No CBAM default value found for CN code {req.cn_code}")
        factor_direct = dv.direct_emissions_factor * (1 + dv.markup_pct / 100)
        factor_indirect = dv.indirect_emissions_factor * (1 + dv.markup_pct / 100)
        direct_t = round(req.quantity_t * factor_direct, 3)
        indirect_t = round(req.quantity_t * factor_indirect, 3)
        source = models.EmissionSource.DEFAULT_VALUE

    good_name = (
        db.query(models.CbamDefaultValue.good_name)
        .filter_by(cn_code=req.cn_code)
        .limit(1)
        .scalar()
        or req.cn_code
    )

    record = models.CbamGoodsImport(
        declarant_id=req.declarant_id,
        cn_code=req.cn_code,
        good_name=good_name,
        country_of_origin=req.country_of_origin,
        quantity_t=req.quantity_t,
        import_date=req.import_date,
        emission_source=source,
        direct_emissions_t=direct_t,
        indirect_emissions_t=indirect_t,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/declarations", response_model=list[schemas.CbamDeclarationOut])
def list_declarations(
    declarant_id: int | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    org_ids = get_my_org_ids(db, user.tenant_id)
    q = (
        db.query(models.CbamDeclaration)
        .join(models.CbamDeclarant, models.CbamDeclaration.declarant_id == models.CbamDeclarant.id)
        .filter(models.CbamDeclarant.org_id.in_(org_ids))
    )
    if declarant_id:
        q = q.filter(models.CbamDeclaration.declarant_id == declarant_id)
    return q.all()


@router.post("/declarations/{declarant_id}/{year}/{quarter}/reconcile", response_model=schemas.CbamDeclarationOut)
def reconcile_declaration(
    declarant_id: int,
    year: int,
    quarter: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    """Data Reconciliation for Monitoring & Control: roll up the quarter's imports
    into one declaration and net off certificates already held."""
    _require_declarant_in_tenant(db, declarant_id, user.tenant_id)

    imports = (
        db.query(models.CbamGoodsImport)
        .filter(
            models.CbamGoodsImport.declarant_id == declarant_id,
            models.CbamGoodsImport.import_date >= f"{year}-{(quarter - 1) * 3 + 1:02d}-01",
            models.CbamGoodsImport.import_date < f"{year if quarter < 4 else year + 1}-{(quarter * 3) % 12 + 1:02d}-01",
        )
        .all()
    )
    total_emissions = sum(i.direct_emissions_t + i.indirect_emissions_t for i in imports)

    held_certs = (
        db.query(models.CbamCertificate)
        .filter_by(declarant_id=declarant_id, status=models.CbamCertificateStatus.HELD)
        .all()
    )
    available_cert_qty = sum(c.quantity_t_co2 for c in held_certs)
    surrendered = min(total_emissions, available_cert_qty)

    remaining = surrendered
    for c in held_certs:
        if remaining <= 0:
            break
        take = min(c.quantity_t_co2, remaining)
        if take >= c.quantity_t_co2:
            c.status = models.CbamCertificateStatus.SURRENDERED
        remaining -= take

    decl = db.query(models.CbamDeclaration).filter_by(declarant_id=declarant_id, year=year, quarter=quarter).first()
    if decl is None:
        decl = models.CbamDeclaration(declarant_id=declarant_id, year=year, quarter=quarter, total_embedded_emissions_t=0)
        db.add(decl)

    decl.total_embedded_emissions_t = round(total_emissions, 3)
    decl.certificates_surrendered_t = round(surrendered, 3)
    decl.status = models.CbamDeclarationStatus.RECONCILED
    db.commit()
    db.refresh(decl)
    return decl
