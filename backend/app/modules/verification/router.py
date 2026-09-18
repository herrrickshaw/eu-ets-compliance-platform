from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ... import models, schemas
from ...auth.deps import get_current_user, get_my_org_ids
from ...db import get_db

router = APIRouter(prefix="/api/verification", tags=["Verification"])


def _subject_org_id(db: Session, subject_type: str, subject_id: int) -> int | None:
    """Resolve which Organization owns the thing being verified, so its tenant can
    see the record too (not just the verifier)."""
    if subject_type == models.VerificationSubjectType.EMISSION_REPORT.value:
        report = db.get(models.EmissionReport, subject_id)
        vessel = db.get(models.Vessel, report.vessel_id) if report else None
        return vessel.org_id if vessel else None
    if subject_type == models.VerificationSubjectType.INSTALLATION_COMPLIANCE.value:
        installation = db.get(models.Installation, subject_id)
        return installation.org_id if installation else None
    if subject_type == models.VerificationSubjectType.CREDIT_UNIT_BATCH.value:
        unit = db.get(models.CreditUnit, subject_id)
        return unit.current_owner_org_id if unit else None
    if subject_type == models.VerificationSubjectType.CBAM_DECLARATION.value:
        decl = db.get(models.CbamDeclaration, subject_id)
        declarant = db.get(models.CbamDeclarant, decl.declarant_id) if decl else None
        return declarant.org_id if declarant else None
    return None


@router.get("/records", response_model=list[schemas.VerificationRecordOut])
def list_records(
    status: str | None = None, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)
):
    """Visible to the tenant acting as verifier, and to the tenant whose data is
    being verified (the submitter wants to see the status of their own submission)."""
    org_ids = set(get_my_org_ids(db, user.tenant_id))
    q = db.query(models.VerificationRecord)
    if status:
        q = q.filter(models.VerificationRecord.status == status)
    records = q.all()
    return [
        r
        for r in records
        if r.verifier_org_id in org_ids or _subject_org_id(db, r.subject_type, r.subject_id) in org_ids
    ]


@router.post("/decide", response_model=schemas.VerificationRecordOut)
def decide(req: schemas.VerifyRequest, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    """Stage -> verify -> commit, generalized across subject types (cadt pattern).
    On approval this also advances the underlying subject's own state machine
    (e.g. EmissionReport -> DOC_ISSUED, mirroring THETIS-MRV's Document of Compliance)."""
    verifier_org = db.get(models.Organization, req.verifier_org_id)
    if verifier_org is None or verifier_org.tenant_id != user.tenant_id:
        raise HTTPException(403, "verifier_org_id does not belong to your tenant")

    record = (
        db.query(models.VerificationRecord)
        .filter_by(subject_type=req.subject_type, subject_id=req.subject_id)
        .order_by(models.VerificationRecord.id.desc())
        .first()
    )
    if record is None:
        record = models.VerificationRecord(
            subject_type=req.subject_type,
            subject_id=req.subject_id,
            verifier_org_id=req.verifier_org_id,
        )
        db.add(record)

    record.status = models.VerificationStatus.VERIFIED if req.approve else models.VerificationStatus.NON_CONFORMANCE
    record.findings = req.findings
    record.resolved_at = datetime.utcnow()

    if req.approve:
        if req.subject_type == models.VerificationSubjectType.EMISSION_REPORT.value:
            report = db.query(models.EmissionReport).get(req.subject_id)
            if report:
                report.status = models.EmissionReportStatus.DOC_ISSUED
        elif req.subject_type == models.VerificationSubjectType.CREDIT_UNIT_BATCH.value:
            unit = db.query(models.CreditUnit).get(req.subject_id)
            if unit and unit.status == models.CreditUnitStatus.STAGED:
                unit.status = models.CreditUnitStatus.ISSUED

    db.commit()
    db.refresh(record)
    return record


@router.get("/integrity-stats", response_model=list[schemas.VerificationIntegrityStatOut])
def list_integrity_stats(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    return (
        db.query(models.VerificationIntegrityStat)
        .order_by(models.VerificationIntegrityStat.category, models.VerificationIntegrityStat.id)
        .all()
    )
