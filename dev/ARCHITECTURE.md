# Architecture

How the pieces connect, how a request flows, and where to make changes.

## Two layers + a pipeline

```
CSV exports (bank/CC)  ─┐
                        ▼
   cashflow.py  ──►  all_transactions.csv  ──►  monthly reports (xlsx)
   portfolio.py ──►  Portfolio_Report.xlsx
                        │
                        ▼
   FastAPI backend (backend/app)  ──►  JSON over HTTP  ──►  Next.js frontend
        routers → services                                    (dashboard pages)
```

1. **Ingest pipeline** (Python, runs offline): `cashflow.py` reads each account's CSV, normalizes to a unified schema, tags `flow_type`, classifies category/subcategory, and writes `CashFlow/all_transactions.csv` plus monthly summaries. `portfolio.py` reads holdings and writes `InvestmentPortfolio/Portfolio_Report.xlsx`.
2. **Backend API** (FastAPI): reads the pipeline outputs + JSON config (`accounts.json`, `budgets.json`, `transaction_notes.json`) from the active data directory and serves them. `routers/` are thin; `services/` hold the logic.
3. **Frontend** (Next.js): app-router pages fetch the API and render charts (Recharts).

## Data directory resolution

`config.py` reads `DATA_MODE` (`demo` | `production`), then sets:
- `DATA_DIR` → `Demo/` or `Production/`
- `CASHFLOW_ROOT`, `CASHFLOW_MONTHLY`, `PORTFOLIO_ROOT` under it
- `FAMILY_NAME`, `IS_DEMO` for display

So the same code serves synthetic demo data or the real private data, chosen entirely by one env var.

## Module map (backend)

| Endpoint area | Router | Service | Reads |
|---|---|---|---|
| Accounts | `routers/accounts.py` | `accounts_service.py` | `accounts.json` |
| Balances | `routers/balances.py` | `balances_service.py` | `balances.json` |
| Cash flow | `routers/cashflow.py` | `cashflow_service.py` | `all_transactions.csv` |
| Budget | `routers/budget.py` | `budget_service.py` | `budgets.json` |
| Portfolio | `routers/portfolio.py` | `portfolio_service.py` | `Portfolio_Report.xlsx` |
| Notes | `routers/notes.py` | `notes_service.py` | `transaction_notes.json` |
| Action items | `routers/action_items.py` | `action_items_service.py` | `ActionItems.md` |
| Upload | `routers/upload.py` | (writes CSVs into the data dir) | — |
| Chat | `routers/chat.py` | `chat_service.py` | aggregates the above |

`cashflow_service.py` is the largest service: it applies notes, budgets, and the income/expense filters on top of `all_transactions.csv`.

## Where to make common changes

- **New account CSV format** → add a parser in `cashflow.py` and register it.
- **Recategorize transactions** → classification logic in `cashflow.py` (and the notes/overrides path in `cashflow_service.py`).
- **New dashboard view** → add a page under `frontend/src/app/`, a router + service pair on the backend.
- **Brand/chart colors** → `config.py` `BRAND` / `BRAND_PALETTE`.

## Known constraints

- Pipeline scripts are duplicated in `Demo/` and `Production/`.
- No automated test suite yet.
- CORS is open to `localhost:3000/3001` only (local-first app).
