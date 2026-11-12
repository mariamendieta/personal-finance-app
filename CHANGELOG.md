# Changelog

Notable changes to the app. Newest first. Add an entry when you ship a user-visible change or a meaningful refactor. Dates are when the change landed on `main`.

## Unreleased

- Add Data (Cash Flow upload) tab: file inputs now accept multiple files per account (appended, not replaced) with per-file remove buttons before saving, plus a new "Already Saved This Month" panel listing files already on disk for the month with their own delete buttons. Backend adds `GET /api/upload/cashflow/list` and `DELETE /api/upload/cashflow/file`. Multiple files for the same account now get distinct filenames on save (`_2`, `_3`, ...) instead of overwriting each other.
- Add Data tab: added a Month picker so past months can be backfilled, not just the current one. Options are sourced from a new `GET /api/upload/cashflow/months` endpoint that lists the real folders already on disk (resolving both the current `YYYY-MM_Mon` naming convention and the older `MonYY` short form), so a selection always points at the actual existing folder for that month instead of risking a second, disconnected folder with a guessed name.
- New Coverage tab on the Cash Flow page: a grid of every account cashflow.py has ever recognized (including untracked cards not yet in `accounts.json`) against every calendar month that actually has a transaction dated that month — computed from real parsed transaction dates, not from which folder a file happens to sit in (uploads commonly lag a month or more, so a file in e.g. "Nov26" often holds October-or-earlier data; grouping by folder name would have misreported that as November coverage). Backed by a new `GET /api/upload/cashflow/coverage` endpoint.
- Coverage tab: added a "Not used" checkbox per account to mark cards/accounts that have been retired, so their missing months stop showing up as gaps — they're collapsed into a separate, dimmed subsection instead. Backed by a new `PUT /api/upload/cashflow/coverage/ignore` endpoint and a `coverage_ignored.json` data file.
- Add Data tab: "Already Saved This Month" now shows each file's actual parsed transaction date range next to its name (e.g. `September2026_0998.csv (2026-08-19 – 2026-09-11)`), so it's clear at a glance what a file really covers instead of having to infer it from the filename or which folder it's sitting in.
- Cash Flow dashboard: the Time Period selector (YTD / last month / 3mo / 6mo / 12mo) now controls the summary cards and the main charts (Monthly Outflows, Income by Source, Net Income), not just the detail tables below. Previously those were hardcoded to a fixed 12-month window regardless of the selector.
- The household pipeline scripts moved out of this public repo into the private woffieta-data repo; `Production/` is no longer tracked. `Demo/` scripts scrubbed of household-specific rules (demo output unchanged except the car-lease subcategory label). Household vendor names now load from the private `classification_overrides.json` (`vendor_rules`). Added a public-repo denylist check (`scripts/check-public-denylist.sh`, hooks in `.githooks/`).
- Added contributor/agent docs: `CLAUDE.md`, `dev/ARCHITECTURE.md`, `dev/OBJECTIVE.md`, and this changelog.

## 2026-07-06

- Shrunk the Unclassified bucket: 15 new CATEGORY_RULES patterns in `Production/cashflow.py` for the known 2026 leftovers (BoA fee descriptors, Speedway / Premium Parking, TSA PreCheck / onboard wi-fi, the May Spain-trip tail, Prime Video / GoDaddy / Google-guitar subscriptions, AMZNPharma, plus 7 Scott-decided judgment calls: BIG 5 → Fitness & Healthcare, Office Depot + Bookish → Shopping, SJC Mi Casa → Travel, Duane's Garden Patch → House & Maintenance, USPS → Fees & Bank Charges, DeLaurenti → Restaurants). 2026 Unclassified YTD drops $3,796 → $2,434; the remainder is all Venmo, which has no recipient in the CSV description and is handled via the monthly Unclassified review + `transaction_notes.json`. Also moved the dead `\bHM ES\b` Shopping pattern to Travel (its word boundary never matched the store-numbered `HM ES0200` form). Production only: Demo's rule block has already diverged and its synthetic data has none of these merchants.
- `refresh_forecast_sheet.py`: House row 30 desc-filter extended to cover a second house helper; row renamed in the Sheet's Monthly + Map tabs.
- Add `Production/refresh_forecast_sheet.py` — writes one closed month of pipeline actuals + SoFi balances into the Woffieta Forecast Google Sheet (run after cashflow.py; see woffieta-data/Forecast/requirements.md).

## 2026-04-22

- Investment metrics added; Luthien-expense reclassification rule; instructions page updates.

## 2026-04-16

- Category filtering and tier organization in the cash-flow view; Work Travel / Luthien transaction classification.

## 2026-03-19

- Restructured the repo as `personal-finance-app` (code) with a separate private data repo.
- New card parsers and improved transaction classification; transaction notes.

## 2026-03-18

- Initial React + Next.js frontend and FastAPI backend; action items; brand colors.

## 2026-03-10

- Initial finance dashboard with code and demo data; sidebar nav, time-period filter, features backlog.
