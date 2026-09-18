# Carbon Compliance & Trading Platform

A modular, multi-tenant prototype covering **EU ETS** (including the 2024
shipping/maritime extension), **CBAM**, carbon credit sourcing, MRV
verification, trading, and an **India CCTS** market module — one platform
with a shared accounting spine, JWT auth, and per-tenant data isolation.

**All data is illustrative/sample data, seeded for demonstration.** It is not
a live feed and not a certified compliance tool. Do not use it to make actual
EU ETS, CBAM, MRV, or CCTS filings. The India module in particular is sourced
from a research pass over secondary reporting, not primary gazette text or any
official API — see [`docs/INDIA_CCTS_SOURCES.md`](docs/INDIA_CCTS_SOURCES.md)
for exactly what is and isn't verified.

## Architecture

Each module's data model and workflow is deliberately borrowed from a real
reference system rather than invented from scratch — see the module
docstring in [`backend/app/models.py`](backend/app/models.py) for the full
mapping.

| Module | Modeled on |
|---|---|
| **Auth & multi-tenancy** | JWT bearer auth; every `Organization` belongs to a `Tenant` (the login/billing boundary) |
| **EU ETS core** | EU Union Registry — operator holding accounts, free allocation, surrender |
| **Shipping MRV** | EMSA THETIS-MRV — Monitoring Plan → Emission Report → Verifier → Document of Compliance |
| **CBAM** | CBAM Transitional Registry — Trader Portal / Authorisation Management / Data Reconciliation |
| **Credit sourcing** | Chia-Network/cadt (Climate Action Data Trust) — program → project → issuance → unit, staged-write |
| **Verification** | cadt's stage → verify → commit pattern, generalized across ETS/shipping/CBAM/credits |
| **Trading** | One order book / position ledger shared across EUAs, CBAM certificates, and voluntary credits |
| **India CCTS** | BEE/MoEFCC's GHG Emission Intensity targets (demand) vs. Article 6.2 eligible activities (supply), plus comparative KR/CN/JP/EU carbon pricing |

### Multi-tenancy model

A `Tenant` is a logged-in customer account (one per company in the demo seed).
Every `Organization` (installation operator, shipping company, CBAM declarant,
credit developer, trader, verifier) belongs to exactly one tenant. Private
data — installations, vessels, declarants, compliance status, positions — is
always scoped to the caller's tenant. Cross-tenant market data — the org
directory, credit-project listings, the trading order book/price history, and
the India CCTS reference data — is visible to any authenticated user, mirroring
how a real marketplace/exchange works (you need to see counterparties and
public order books, but not their private compliance data). See each router's
`get_my_org_ids` usage for exactly what's scoped vs. global.

## Running it

Backend (FastAPI + SQLite):

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed.seed_data   # (re)seeds illustrative data — drops existing tables,
                                # prints demo tenant logins (password: demo1234)
uvicorn app.main:app --port 8000
```

Frontend (React + Vite + Tailwind):

```bash
cd frontend
npm install
npm run dev -- --port 5174   # proxies /api to localhost:8000
```

Open http://localhost:5174, log in with any printed demo account (or register a
new tenant), and use the tab bar. API docs: http://127.0.0.1:8000/docs

## Layout

```
backend/app/
  models.py                shared SQLAlchemy schema, all modules
  schemas.py                Pydantic request/response models
  auth/                      security.py (hashing/JWT), deps.py (current-user +
                             tenant-scoping helpers), router.py (register/login/me)
  modules/<name>/router.py   one FastAPI router per module
  seed/seed_data.py         illustrative seed data + demo tenants/users
frontend/src/
  auth.jsx                   AuthProvider/useAuth — session, login, register, logout
  pages/Login.jsx            login/register screen with demo-account shortcuts
  pages/<Name>.jsx           one dashboard page per module
  components/                shared table/card/badge/sparkline UI
docs/
  INDIA_CCTS_SOURCES.md      sourcing/confidence notes for the India module
```
