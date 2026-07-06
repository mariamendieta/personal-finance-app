# Changelog

Notable changes to the app. Newest first. Add an entry when you ship a user-visible change or a meaningful refactor. Dates are when the change landed on `main`.

## Unreleased

- Added contributor/agent docs: `CLAUDE.md`, `dev/ARCHITECTURE.md`, `dev/OBJECTIVE.md`, and this changelog.

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
- 2026-07-06: Add Production/refresh_forecast_sheet.py — writes one closed month of pipeline actuals + SoFi balances into the Woffieta Forecast Google Sheet (run after cashflow.py; see woffieta-data/Forecast/requirements.md).
