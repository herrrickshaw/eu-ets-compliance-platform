import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..db import get_db
from .deps import get_current_user
from .security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "tenant"


@router.post("/register", response_model=schemas.TokenResponse)
def register(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    if db.query(models.User).filter_by(email=req.email).first():
        raise HTTPException(400, "Email already registered")

    base_slug = _slugify(req.tenant_name)
    slug = base_slug
    n = 1
    while db.query(models.Tenant).filter_by(slug=slug).first():
        n += 1
        slug = f"{base_slug}-{n}"

    tenant = models.Tenant(name=req.tenant_name, slug=slug)
    db.add(tenant)
    db.flush()

    user = models.User(
        tenant_id=tenant.id,
        email=req.email,
        hashed_password=hash_password(req.password),
        role=models.UserRole.OWNER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(tenant)

    token = create_access_token(user.id, tenant.id)
    return schemas.TokenResponse(access_token=token, user=user, tenant=tenant)


@router.post("/login", response_model=schemas.TokenResponse)
def login(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter_by(email=req.email).first()
    if user is None or not verify_password(req.password, user.hashed_password):
        raise HTTPException(401, "Invalid email or password")

    tenant = db.get(models.Tenant, user.tenant_id)
    token = create_access_token(user.id, tenant.id)
    return schemas.TokenResponse(access_token=token, user=user, tenant=tenant)


@router.get("/me", response_model=schemas.MeResponse)
def me(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    tenant = db.get(models.Tenant, user.tenant_id)
    return schemas.MeResponse(user=user, tenant=tenant)
