# Carbon Compliance & Trading Platform

A modular prototype covering **EU ETS** (including the 2024 shipping/maritime
extension), **CBAM**, carbon credit sourcing, MRV verification, and trading —
in one platform with a shared accounting spine.

**All data is illustrative/sample data, seeded for demonstration.** It is not
a live feed and not a certified compliance tool. Do not use it to make actual
EU ETS, CBAM, or MRV filings.

## Architecture

Each module's data model and workflow is deliberately borrowed from a real
reference system rather than invented from scratch — see the module
docstring in [`backend/app/models.py`](backend/app/models.py) for the full
mapping, and each module's own README section below.

| Module | Modeled on |
|---|---|
| **EU ETS core** | EU Union Registry — operator holding accounts, free allocation, surrender |
| **Shipping MRV** | EMSA THETIS-MRV — Monitoring Plan → Emission Report → Verifier → Document of Compliance |
| **CBAM** | CBAM Transitional Registry — Trader Portal / Authorisation Management / Data Reconciliation |
| **Credit sourcing** | Chia-Network/cadt (Climate Action Data Trust) — program → project → issuance → unit, staged-write |
| **Verification** | cadt's stage → verify → commit pattern, generalized across ETS/shipping/CBAM/credits |
| **Trading** | One order book / position ledger shared across EUAs, CBAM certificates, and voluntary credits |

## Running it

Backend (FastAPI + SQLite):

```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed.seed_data   # (re)seeds illustrative data — drops existing tables
uvicorn app.main:app --port 8000
```

Frontend (React + Vite + Tailwind):

```bash
cd frontend
npm install
npm run dev -- --port 5174   # proxies /api to localhost:8000
```

API docs: http://127.0.0.1:8000/docs

## Layout

```
backend/app/
  models.py            shared SQLAlchemy schema, all 6 modules
  schemas.py            Pydantic request/response models
  modules/<name>/router.py   one FastAPI router per module
  seed/seed_data.py     illustrative seed data
frontend/src/
  pages/<Name>.jsx       one dashboard page per module
  components/            shared table/card/badge/sparkline UI
```
