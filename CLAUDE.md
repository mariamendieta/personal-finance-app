# Personal Finance App: Contributor & Agent Guide

> **THIS REPO IS PUBLIC.** Never put household names, amounts, employers, card numbers, income sources or other private details in code, comments, commit messages, docs or demo data. Household-specific rules and data belong in the private `woffieta-data` repo. A pre-commit hook enforces this (see "Public-repo check" below).

Guidance for anyone (human or AI agent) working in this repo. Read `dev/ARCHITECTURE.md` first when you need to understand how requests flow or where to make a change.

## Purpose & scope

- A personal finance tracker: it ingests bank and credit-card CSV exports, classifies every transaction, and serves cash-flow and investment dashboards.
- Stack: FastAPI backend (Python) plus Next.js 15 frontend (React, Tailwind, Recharts). Data processing is pandas; config/notes are JSON.
- **This repo holds generic code only.** Private financial data, and the household's own pipeline scripts, live in the private `woffieta-data` repo (see below).

## Sibling repo (private data)

- **woffieta-data** (`github.com/mariamendieta/woffieta-data`) is the private data + analysis repo. Clone it next to this repo (`~/build/woffieta-data`); `run-production.sh` finds it there, or set `PRODUCTION_DATA_DIR`. It holds the monthly transaction CSVs, `balances.json`, generated reports, and analysis docs (`FinancialSummary.md`, `FamilyFinancialSystemPlan.md`).
- The household pipeline scripts (`cashflow.py`, `portfolio.py`, `generate_report.py`, `dashboard.py`, `refresh_forecast_sheet.py`, `venmo_classify.py`) are tracked in woffieta-data, because they hold household-specific rules. The backend runs them from the data directory. `Demo/` here carries the generic copies.
- Cross-repo work: when a code change needs a data-format change, describe it in this repo's PR and link the data-repo change, rather than splitting context across two PRs.

## Repo layout

- `backend/app/` — FastAPI. `routers/` are thin HTTP endpoints that call `services/` (all logic). `config.py` resolves `DATA_MODE` to the data directory and family name.
- `frontend/src/app/` — Next.js app-router pages: `cashflow`, `budget`, `investments`, `action-items`, `instructions`.
- `Demo/` — synthetic data ("Viviana and Michael") plus the generic pipeline scripts (`cashflow.py`, `portfolio.py`, `generate_report.py`, `dashboard.py`).
- Production data and scripts are not in this repo; see the sibling repo above.
- `FeaturesBacklog.md` — feature ideas and status. `BrandGuidelines/` — brand assets.

## Data modes

`DATA_MODE=demo` (default) reads `Demo/`; `DATA_MODE=production` reads `PRODUCTION_DATA_DIR` (the woffieta-data clone). `config.py` picks the data directory and family name from this env var.

## How to run

- Demo: `DATA_MODE=demo python3 -m uvicorn backend.app.main:app --port 8000`, then `cd frontend && npm run dev -- -p 3001`.
- Production: `./run-production.sh` (backend on 8001, frontend on 3001).
- Regenerate reports from CSVs: `cd ~/build/woffieta-data && python3 cashflow.py` (then `portfolio.py` / `generate_report.py` as needed).

## The transaction pipeline (the heart of the app)

`cashflow.py` parses each account's CSV format, normalizes to one schema, and tags every row with a **flow_type** so card payments and transfers are never double-counted:

- `spending` — a real purchase or bill (this is what counts as an expense)
- `income` — paycheck, deposit, interest, reimbursement
- `cc_payment` — a credit-card payment (appears on both sides; exclude both)
- `internal_transfer` — movement between your own accounts (exclude)
- `other` — fees, uncategorized (review manually)

It then classifies `spending` into category and subcategory. Output is `CashFlow/all_transactions.csv` in the data directory, plus monthly reports. Any "why is the total X?" reconciliation starts from flow_type (a raw account-outflow total double-counts card payments and transfers).

## Conventions

- Keep routers thin; put logic in services.
- Use the brand palette in `config.py` for any chart or UI color.
- Pipeline scripts are duplicated: the generic copy in `Demo/` here, the household copy in woffieta-data. If you change generic pipeline logic, change both (known debt). Household-specific rules go only in woffieta-data: its scripts or `classification_overrides.json` (category, subcategory and `vendor_rules`).
- There are no automated tests yet. Adding them is welcome; flag behavior you change manually.

## Public-repo check

A pre-commit and commit-msg hook (`scripts/check-public-denylist.sh`) blocks any commit whose added lines or message contain a term from the private denylist `public-repo-denylist.txt` in the woffieta-data clone. Enable it once per clone with `git config core.hooksPath .githooks`. The hook warns and skips if it can't find the denylist, so contributors without the data repo aren't blocked. Run `scripts/check-public-denylist.sh --history` to scan the whole history.

## Development workflow

1. Work against the current objective in `dev/OBJECTIVE.md`.
2. Read `dev/ARCHITECTURE.md` for request flow and the module map.
3. Update `CHANGELOG.md` when you ship a user-visible change.
4. Merging directly to `main` is fine — that is Maria's guidance for both this repo and woffieta-data. Open a PR for bigger or higher-risk changes (preferred but optional). Keep changes small either way.

## Objective placement (which repo owns an objective)

Home an objective where its primary artifacts live, so it never has to be asked again:

- **App code** (a dashboard view, pipeline change, API endpoint, bug fix) → this repo's `dev/OBJECTIVE.md`.
- **Forecasts, data, or analysis** (forecast comparisons, Excel-model work, cost-of-living analysis) → woffieta-data `OBJECTIVE.md`.
- A **cross-repo** objective is homed by its primary artifacts, with a one-line pointer from the other repo's `OBJECTIVE.md`.
