# Personal Finance App: Contributor & Agent Guide

Guidance for anyone (human or AI agent) working in this repo. Read `dev/ARCHITECTURE.md` first when you need to understand how requests flow or where to make a change.

## Purpose & scope

- A personal finance tracker: it ingests bank and credit-card CSV exports, classifies every transaction, and serves cash-flow and investment dashboards.
- Stack: FastAPI backend (Python) plus Next.js 15 frontend (React, Tailwind, Recharts). Data processing is pandas; config/notes are JSON.
- **This repo holds code only.** Private financial data lives in a separate repo cloned into `Production/` (see below).

## Sibling repo (private data)

- **woffieta-data** (`github.com/mariamendieta/woffieta-data`) is the private data + analysis repo. Clone it into `Production/`. It holds the monthly transaction CSVs, `balances.json`, generated reports, and analysis docs (`FinancialSummary.md`, `FamilyFinancialSystemPlan.md`).
- The data repo gitignores `*.py`, so the pipeline scripts (which live HERE, in `Production/` and `Demo/`) coexist with the data when the data repo is cloned in.
- Cross-repo work: when a code change needs a data-format change, describe it in this repo's PR and link the data-repo change, rather than splitting context across two PRs.

## Repo layout

- `backend/app/` — FastAPI. `routers/` are thin HTTP endpoints that call `services/` (all logic). `config.py` resolves `DATA_MODE` to the data directory and family name.
- `frontend/src/app/` — Next.js app-router pages: `cashflow`, `budget`, `investments`, `action-items`, `instructions`.
- `Demo/` and `Production/` — per-mode data directories. Each carries its own copy of the pipeline scripts (`cashflow.py`, `portfolio.py`, `generate_report.py`, `dashboard.py`).
- `Demo/` ships synthetic data ("Viviana and Michael"); `Production/` is the cloned private data repo (real "Woffieta Family" data).
- `FeaturesBacklog.md` — feature ideas and status. `BrandGuidelines/` — brand assets.

## Data modes

`DATA_MODE=demo` (default) reads `Demo/`; `DATA_MODE=production` reads `Production/`. `config.py` picks the data directory and family name from this env var.

## How to run

- Demo: `DATA_MODE=demo python3 -m uvicorn backend.app.main:app --port 8000`, then `cd frontend && npm run dev -- -p 3001`.
- Production: `./run-production.sh` (backend on 8001, frontend on 3001).
- Regenerate reports from CSVs: `cd Production && python3 cashflow.py` (then `portfolio.py` / `generate_report.py` as needed).

## The transaction pipeline (the heart of the app)

`cashflow.py` parses each account's CSV format, normalizes to one schema, and tags every row with a **flow_type** so card payments and transfers are never double-counted:

- `spending` — a real purchase or bill (this is what counts as an expense)
- `income` — paycheck, deposit, interest, reimbursement
- `cc_payment` — a credit-card payment (appears on both sides; exclude both)
- `internal_transfer` — movement between your own accounts (exclude)
- `other` — fees, uncategorized (review manually)

It then classifies `spending` into category and subcategory. Output is `Production/CashFlow/all_transactions.csv` plus monthly reports. Any "why is the total X?" reconciliation starts from flow_type (a raw account-outflow total double-counts card payments and transfers).

## Conventions

- Keep routers thin; put logic in services.
- Use the brand palette in `config.py` for any chart or UI color.
- Pipeline scripts are currently duplicated in `Demo/` and `Production/`. If you change pipeline logic, change both, or factor out the duplication (known debt).
- There are no automated tests yet. Adding them is welcome; flag behavior you change manually.

## Development workflow

1. Work against the current objective in `dev/OBJECTIVE.md`.
2. Read `dev/ARCHITECTURE.md` for request flow and the module map.
3. Update `CHANGELOG.md` when you ship a user-visible change.
4. Merging directly to `main` is fine — that is Maria's guidance for both this repo and woffieta-data. Open a PR for bigger or higher-risk changes (preferred but optional). Keep changes small either way.
