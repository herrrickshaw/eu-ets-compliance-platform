from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .auth.deps import get_current_user
from .auth.router import router as auth_router
from .db import Base, engine, get_db
from .modules.cbam.router import router as cbam_router
from .modules.credits.router import router as credits_router
from .modules.ets_core.router import router as ets_router
from .modules.india_ccts.router import router as india_router
from .modules.shipping_mrv.router import router as shipping_router
from .modules.trading.router import router as trading_router
from .modules.verification.router import router as verification_router

app = FastAPI(
    title="Carbon Compliance & Trading Platform",
    description="EU ETS (incl. shipping) + CBAM compliance, carbon credit sourcing, "
    "MRV verification, and trading in one platform. Illustrative/sample data only.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth endpoints (register/login) are public; every other module requires a
# bearer token, and each module router does its own tenant-scoping on top.
app.include_router(auth_router)
for r in (ets_router, shipping_router, cbam_router, credits_router, verification_router, trading_router, india_router):
    app.include_router(r, dependencies=[Depends(get_current_user)])


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/orgs", response_model=list[schemas.OrganizationOut], tags=["Shared"])
def list_orgs(db: Session = Depends(get_db), _user: models.User = Depends(get_current_user)):
    """Cross-tenant directory (counterparties, verifiers, credit developers need to be
    resolvable by name across tenants) — requires login, but is not tenant-filtered."""
    return db.query(models.Organization).all()
