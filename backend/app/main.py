from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .db import Base, engine, get_db
from .modules.cbam.router import router as cbam_router
from .modules.credits.router import router as credits_router
from .modules.ets_core.router import router as ets_router
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
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (ets_router, shipping_router, cbam_router, credits_router, verification_router, trading_router):
    app.include_router(r)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/orgs", response_model=list[schemas.OrganizationOut], tags=["Shared"])
def list_orgs(db: Session = Depends(get_db)):
    return db.query(models.Organization).all()
