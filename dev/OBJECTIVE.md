# Current Objective

This file holds the single objective currently being worked on, in the spirit of an agent-driven workflow: an agent (or contributor) reads it, does the work, updates `CHANGELOG.md`, and clears or replaces this objective.

## How to use

- One objective at a time. Keep it concrete and verifiable ("add X view", "fix Y double-count", "refactor Z").
- Longer-horizon ideas live in `FeaturesBacklog.md`; the family-level plan lives in woffieta-data `FamilyFinancialSystemPlan.md`.
- When done: summarize in `CHANGELOG.md` and reset this to the next objective.

## Objective

**Shrink the Unclassified bucket: add CATEGORY_RULES for the known 2026 leftovers** (set 2026-07-06; context: [Forecast Sheet cell audit](https://github.com/mariamendieta/woffieta-data/blob/main/analysis/2026-07-06_forecast-sheet-cell-audit.md), "Other" bucket discussion with Scott).

Where: `Production/cashflow.py` `CATEGORY_RULES` (ordered regex list, first match wins, fall-through = Unclassified; rules are retroactive on rerun). Change `Demo/cashflow.py` too if the rule blocks are shared (known duplication debt, see `CLAUDE.md`).

Confident rules to add (2026 Unclassified, $ = YTD through June):

| Pattern | Category | Items |
|---|---|---|
| `LATE FEE FOR PAYMENT DUE\|INTEREST CHARGED ON PURCHASES\|ANNUAL MEMBERSHIP FEE` | Fees & Bank Charges | $174 (BoA returned-payment fees, waived, + card fee) |
| `SPEEDWAY` | Car | $86 gas |
| `PREMIUM PARKING` | Car | $9 |
| `TSA PRECHECK\|WI-FI ONBOARD` | Travel | $95 |
| `H\. BARCELONA\|FLORENCIA RAMBLA\|HM ES\|SUMUP\|ESPASA CALPE\|BACALLANERIES` | Travel | $687 Spain-trip tail (May) |
| `Prime Video\|Google Ultimate Guita\|GODADDY` | Subscriptions | $65 |
| `AMZNPharma` | Fitness & Healthcare | $22 |

Judgment calls (ask Scott/Maria or leave Unclassified): BIG 5 ($52, Shopping?), OFFICE DEPOT ($51), USPS ($22), DUANE'S GARDEN PATCH ($29, yard?), DELAURENTI ($12, groceries/restaurants?), BOOKISH ($16), SJC MI CASA ($41). **VENMO ($2,434, the biggest chunk) cannot be auto-ruled**: outgoing Venmo has no recipient in the CSV description; handle via the monthly Unclassified review + `transaction_notes.json`.

Verify: rerun `python3 cashflow.py`, then confirm the 2026 Unclassified YTD total drops from ~$3.8k to roughly the VENMO + judgment remainder. Downstream: the [Woffieta Forecast Sheet](https://docs.google.com/spreadsheets/d/1ylY5nD6Tfo2KtGeb3s98_A4Qlh6DwgeBng6XnCayUmM/edit)'s "Other" row shrinks automatically at the next monthly refresh (`Production/refresh_forecast_sheet.py`, single-month scope); already-written black months in the Sheet only change if deliberately re-run with `--month`, which is fine if Scott wants history restated on the improved rules. The Sheet's hidden Map tab documents the row routing; its rules don't need changes (they route by pipeline category, which is exactly what improves here). One exception is Sheet-side, not pipeline-side: Zelles to Adriana / Silvia Adriana ($125) and NUTONE dry cleaners ($42) are already House & Maintenance in the pipeline but land in the Sheet's Other row because the Sheet's House desc-filters (Graciela/Iris/Israel/Francisco) don't match them; if they should roll up to a House row, extend the desc-filter in `refresh_forecast_sheet.py` RULES + the Map tab.

A related app-code item is on deck if/when the forecast objective reaches phase 3 (optional mirror): build a cash-flow projection / run-rate forecast view in the dashboard. Note Maria already has a local (unpushed) run-rate forecast view — push and build on that rather than starting fresh.
