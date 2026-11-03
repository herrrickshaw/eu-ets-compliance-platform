# Carbon Compliance & Trading Platform

<!-- how-to-use-with-ai -->
> **New here?** See [How to use this repo with AI (Claude, Gemini, ChatGPT)](HOW_TO_USE_WITH_AI.md) — clone it, paste it into an AI tool, and ask in plain English.

A modular, multi-tenant prototype covering **EU ETS** (including the 2024 shipping/maritime extension),
**CBAM**, carbon credit sourcing, MRV verification, trading, and an **India CCTS** market module. One FastAPI +
SQLite backend with a shared accounting spine, JWT auth and per-tenant data isolation, plus a React dashboard
with one page per module. It produces JSON API responses (OpenAPI docs at `/docs`) and a browser UI over seeded demo data.

> Status: illustrative prototype (research-only). **All data is illustrative/sample data, seeded for demonstration** —
> not a live feed and not a certified compliance tool. Do not use it for actual EU ETS, CBAM, MRV or CCTS filings.
> The India module is sourced from a research pass over secondary reporting, not primary gazette text or any
> official API — see [`docs/INDIA_CCTS_SOURCES.md`](docs/INDIA_CCTS_SOURCES.md) for what is and isn't verified.

## What it does
- EU ETS core: operator holding accounts, free allocation and allowance surrender (modeled on the EU Union Registry).
- Shipping MRV: monitoring plans, voyages and emission reports; intra-EU legs weighted 100% and extra-EU legs 50% for ETS exposure.
- CBAM: goods imports with default-value mark-up or actual verified emissions, quarterly reconciliation against held certificates, and phase-in demand analysis/projection.
- Credit sourcing and verification: program → project → issuance → unit with a stage → verify → commit pattern (modeled on Chia cadt).
- Trading: one order book and position ledger for EUAs, CBAM certificates and voluntary credits, with price-time-priority matching.
- India CCTS: sector demand model, Article 6.2 supply proxy, gap analysis, comparative carbon prices and capacity-to-credits estimates.

## Quick start
```bash
git clone https://github.com/herrrickshaw/eu-ets-compliance-platform.git
cd eu-ets-compliance-platform/backend
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

Open http://localhost:5174, log in with any printed demo account (or register a new tenant) and use the tab bar.
API docs: http://127.0.0.1:8000/docs

## How it works
Each module's data model and workflow is borrowed from a real reference system rather than invented; the
module docstring in [`backend/app/models.py`](backend/app/models.py) holds the full mapping.

| Module | Modeled on | Code |
|---|---|---|
| Auth & multi-tenancy | JWT bearer auth; every `Organization` belongs to a `Tenant` | `auth/` |
| EU ETS core | EU Union Registry | `modules/ets_core` |
| Shipping MRV | EMSA THETIS-MRV (Monitoring Plan → Emission Report → Verifier → DoC) | `modules/shipping_mrv` |
| CBAM | CBAM Transitional Registry | `modules/cbam` |
| Credit sourcing | Chia-Network/cadt | `modules/credits` |
| Verification | cadt stage → verify → commit, generalized across modules | `modules/verification` |
| Trading | One order book shared across EUAs, CBAM certificates and credits | `modules/trading` |
| India CCTS | BEE/MoEFCC GHG Emission Intensity targets vs. Article 6.2 eligible activities, plus KR/CN/JP/EU pricing | `modules/india_ccts` |

Request flow: `router.py` (HTTP, auth, tenant scoping, DB access) → `service.py` (pure calculations, no DB) where
a module has one (`cbam`, `trading`, `india_ccts`, `shipping_mrv`).

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

## Repository layout
| Path | Purpose |
|---|---|
| `backend/app/models.py`, `schemas.py` | Shared SQLAlchemy schema (all modules) and Pydantic request/response models |
| `backend/app/auth/` | `security.py` (hashing/JWT), `deps.py` (current user, tenant scoping), `router.py` (register/login/me) |
| `backend/app/modules/<name>/router.py` | One FastAPI router per module |
| `backend/app/modules/{cbam,trading,india_ccts,shipping_mrv}/service.py` | Pure calculation/matching logic extracted from the routers |
| `backend/app/seed/seed_data.py` | Illustrative seed data and demo tenants/users |
| `frontend/src/` | `auth.jsx`, `pages/<Name>.jsx` (one per module), shared `components/` |
| `tests/` | pytest suite: API characterisation against a committed golden file, plus service unit tests |
| `docs/` | `INDIA_CCTS_SOURCES.md` sourcing notes; `references/` third-party PDF |
| `graphify-out/` | Generated knowledge-graph output (not hand-written) |

## Data sources
All seeded values are illustrative. The India module draws on secondary reporting and cites sources per row
(`source_note` / `source_name`); see [`docs/INDIA_CCTS_SOURCES.md`](docs/INDIA_CCTS_SOURCES.md). No network
calls are made at runtime or in tests.

## Configuration
| Variable | Default | Purpose |
|---|---|---|
| `JWT_SECRET` | demo-only insecure value in `auth/security.py` | Signing key for access tokens — set your own for anything beyond a local demo |
| `CARBON_DB_PATH` | `backend/carbon_platform.db` | SQLite file location (used by the tests) |

No credentials are required or committed.

## Testing
```bash
pip install pytest ruff httpx -r backend/requirements.txt
pytest -q
ruff check backend tests
```

## Limitations and known issues
- Demo data only; the seeded password for every demo account is public (`demo1234`).
- The default `JWT_SECRET` is an insecure demo value; CORS allows only localhost origins.
- The India module is not an official BEE/MoEFCC figure set; fertilizer status is contested and iron & steel is draft in the seed (see the sourcing notes).
- Backend targets Python 3.11 (routers use `X | None` annotations that FastAPI evaluates at runtime).
- Startup uses the deprecated FastAPI `on_event` hook and `datetime.utcnow`.

## Licence
No licence file yet — all rights reserved.
