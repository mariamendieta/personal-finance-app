# Changelog

Notable changes to the app. Newest first. Add an entry when you ship a user-visible change or a meaningful refactor. Dates are when the change landed on `main`.

## Unreleased

- Added contributor/agent docs: `CLAUDE.md`, `dev/ARCHITECTURE.md`, `dev/OBJECTIVE.md`, and this changelog.

## 2026-07-06

- Shrunk the Unclassified bucket: 15 new CATEGORY_RULES patterns in `Production/cashflow.py` for the known 2026 leftovers (BoA fee descriptors, Speedway / Premium Parking, TSA PreCheck / onboard wi-fi, the May Spain-trip tail, Prime Video / GoDaddy / Google-guitar subscriptions, AMZNPharma, plus 7 Scott-decided judgment calls: BIG 5 → Fitness & Healthcare, Office Depot + Bookish → Shopping, SJC Mi Casa → Travel, Duane's Garden Patch → House & Maintenance, USPS → Fees & Bank Charges, DeLaurenti → Restaurants). 2026 Unclassified YTD drops $3,796 → $2,434; the remainder is all Venmo, which has no recipient in the CSV description and is handled via the monthly Unclassified review + `transaction_notes.json`. Also moved the dead `\bHM ES\b` Shopping pattern to Travel (its word boundary never matched the store-numbered `HM ES0200` form). Production only: Demo's rule block has already diverged and its synthetic data has none of these merchants.
- `Production/refresh_forecast_sheet.py`: House row 30 desc-filter extended to `iris|adriana` so the Silvia Adriana Zelles roll up there; row renamed "Iris + Adriana" in the Sheet's Monthly + Map tabs (Scott's call; NUTONE stays in Other).
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
