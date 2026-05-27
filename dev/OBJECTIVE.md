# Current Objective

This file holds the single objective currently being worked on, in the spirit of an agent-driven workflow: an agent (or contributor) reads it, does the work, updates `CHANGELOG.md`, and clears or replaces this objective.

## How to use

- One objective at a time. Keep it concrete and verifiable ("add X view", "fix Y double-count", "refactor Z").
- Longer-horizon ideas live in `FeaturesBacklog.md`; the family-level plan lives in woffieta-data `FamilyFinancialSystemPlan.md`.
- When done: summarize in `CHANGELOG.md` and reset this to the next objective.

## Objective

Reconcile and right-size the family's 2026+ forecast, in three phases. **Source of truth for forecasts is the Excel LIVE model**; mirroring forecasts into this app is optional (phase 3), not required.

> Note: most of this work happens in the Excel LIVE model and woffieta-data, not in this app. This app's only role is the optional phase-3 mirror. (Placement of this objective is open — see the working notes in woffieta-data.)

### Phase 1 — Compare forecasts (in Excel)

Compare the **LIVE Excel forecast** against a **naive woffieta-data forecast** built purely from per-month run-rate (recent actual monthly spend + known income, projected forward with no curated assumptions). Goal: surface where LIVE's hand-set assumptions diverge from what the actual data implies.

### Phase 2 — Port surgical changes to LIVE

Apply the changes Phase 1 validates (refreshed balances, Maria's Auger income, any run-rate corrections) **into the real Dropbox LIVE files**, surgically. Not a wholesale replacement of the model.

### Phase 3 — Decide the go-forward forecast-management model

Evaluate how to maintain forecasts going forward. **Prior: Excel stays the source of truth**; mirroring or automating into this app is optional / nice-to-have, not a requirement.

**Working inputs (in woffieta-data):** `May23_2026BurnAnalysis.md`, `May27_ExpenseModelReconciliation.md`, and the highlighted working copies in `excel-forecast-refresh-2026-05/` (already hold the refreshed balances + Maria income rebuild ready for the phase-2 port).
