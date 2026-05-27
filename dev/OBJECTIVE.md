# Current Objective

This file holds the single objective currently being worked on, in the spirit of an agent-driven workflow: an agent (or contributor) reads it, does the work, updates `CHANGELOG.md`, and clears or replaces this objective.

## How to use

- One objective at a time. Keep it concrete and verifiable ("add X view", "fix Y double-count", "refactor Z").
- Longer-horizon ideas live in `FeaturesBacklog.md`; the family-level plan lives in woffieta-data `FamilyFinancialSystemPlan.md`.
- When done: summarize in `CHANGELOG.md` and reset this to the next objective.

## Objective

Add a cash-flow projection / scenario view to the dashboard, so the family's forward forecast lives in the app instead of a manual Excel model.

> Best-guess objective inferred from the May 2026 finance work (the 2026 burn forecast and the manual refresh of `Wofford_Cashflow_LIVE.xlsx` / `2030_Scenarios.xlsx`). Confirm or replace before building.

**Context / acceptance criteria:**

- Project monthly and annual net cash flow forward from the classified `spending` data plus known income.
- Support a small scenario matrix (market return × income level), mirroring the existing Excel "2026 Summary" view: e.g. bear / base / bull market returns crossed with income levels.
- Seed inputs from current actuals: Maria's income (Auger, $300k base, started 2026-04-20; ~$215k/yr post-tax), household expenses (~$284k/yr forward, see woffieta-data `FinancialSummary.md`), portfolio $1.62M (non-retirement $1.11M / retirement $0.51M).
- Surface a runway / worst-case burn figure (income vs expenses, draw on the non-retirement portfolio), matching woffieta-data `May23_2026BurnAnalysis.md`.
- Maps to the `FeaturesBacklog.md` "Idea" items: "Cash flow projections" and "Investment scenarios tab."

**Out of scope:**

- Retiring the Excel models outright (parallel-run first).
- Tax modeling beyond effective-rate estimates.
