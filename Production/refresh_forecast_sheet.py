"""Refresh the Woffieta Forecast Google Sheet from pipeline outputs.

Runs after cashflow.py in the monthly cycle (woffieta-data/CLAUDE.md "Adding a
month"). Writes ONLY the cells it owns; never touches gray forecast cells,
formulas, or anything on Summary/Annual:

  - Data tab: fully rewritten (category x month rollups, income, balance snapshots)
  - Monthly row 51 (pipeline spend total, excl Luthien Expenses + Work Travel)
    for ONE month (--month, default: last complete month); single-month scope
    so it never silently overwrites earlier hand-reconciled actuals. Note the
    basis difference: pipeline totals exclude cc payments/transfers and
    Luthien/work-travel; LIVE's ported hand actuals (Jan-Jun 2026) were entered
    on a different basis (e.g. April: pipeline 33,260 vs LIVE 56,000). Decide
    per month which basis wins before re-running over an existing black cell.
  - Monthly rows 42-46 (Restaurants, Groceries, Subscriptions, Fun, Shopping:
    the categories that map 1:1 to pipeline categories; see the Sheet's Map tab)
  - Monthly row 65 (Maria income, desc AUGER INC / CARBON DIRECT)
  - Monthly rows 81-83 (SoFi checking / savings / total actuals from balances.json)

Written cells are flipped to black (actuals); requirements and the black/gray
convention: woffieta-data/Forecast/requirements.md.

Usage (gspread not in the app venv, so run via uv):
  uv run --with gspread python refresh_forecast_sheet.py [--data-dir PATH]
      [--month YYYY-MM] [--dry-run]

Phase 2 (not yet built): per-row category mapping from the Map tab
(house help, childcare splits, utilities), portfolio balances from the
Wofford Portfolio Asset Allocation Sheet into Summary!D6 and Annual!C93/C96.
"""
import argparse, csv, json, re, sys
from pathlib import Path

SHEET_ID = "1ylY5nD6Tfo2KtGeb3s98_A4Qlh6DwgeBng6XnCayUmM"
TOKEN = Path.home() / ".config/mcp-gdrive/credentials-personal.json"
EXCLUDED_CATEGORIES = {"Luthien Expenses", "Work Travel"}  # not personal spend
MARIA_INCOME = re.compile(r"AUGER INC|CARBON DIRECT", re.I)
# Monthly-tab rows whose pipeline category maps 1:1 (Map tab, status "direct")
DIRECT_ROWS = {"Restaurants": 42, "Groceries": 43, "Subscriptions": 44,
               "Fun & Entertainment": 45, "Shopping": 46}
ROW_PIPELINE_TOTAL, ROW_MARIA = 51, 65
ROW_SOFI_CHK, ROW_SOFI_SAV, ROW_SOFI_TOT = 81, 82, 83
MONTH_COL = {m: c for c, m in enumerate(
    ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], start=2)}
BLACK = {"red": 0, "green": 0, "blue": 0}


def default_data_dir():
    for p in [Path(__file__).parent / "woffieta-data", Path.home() / "build/woffieta-data", Path.home() / "woffieta-data"]:
        if (p / "CashFlow/all_transactions.csv").exists():
            return p
    sys.exit("No woffieta-data clone found; pass --data-dir")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--month", help="the closed month to write, YYYY-MM (default: last complete month in the data)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    data_dir = args.data_dir or default_data_dir()

    rows = list(csv.DictReader(open(data_dir / "CashFlow/all_transactions.csv")))
    balances = json.load(open(data_dir / "balances.json"))
    months = sorted({r["date"][:7] for r in rows if r["date"]})
    if args.month:
        month = args.month
    else:
        # last complete month: the latest month is partial unless its last
        # transaction lands on/after the 25th
        last_txn = max(r["date"] for r in rows if r["date"].startswith(months[-1]))
        month = months[-1] if int(last_txn[8:10]) >= 25 else months[-2]
    if month not in months:
        sys.exit(f"No transactions for {month}")
    year, closed = month[:4], [month]

    def spend(month, pred):
        return round(sum(-float(r["amount"]) for r in rows
                         if r["date"][:7] == month and r["flow_type"] == "spending" and pred(r)), 2)

    def income(month, pred):
        return round(sum(float(r["amount"]) for r in rows
                         if r["date"][:7] == month and r["flow_type"] == "income" and pred(r)), 2)

    # ---- assemble Monthly writes: (row, col, value) ----
    writes = []
    for m in closed:
        col = MONTH_COL[m[5:]]
        writes.append((ROW_PIPELINE_TOTAL, col, spend(m, lambda r: r["category"] not in EXCLUDED_CATEGORIES)))
        for cat, row in DIRECT_ROWS.items():
            writes.append((row, col, spend(m, lambda r, cat=cat: r["category"] == cat)))
        writes.append((ROW_MARIA, col, income(m, lambda r: MARIA_INCOME.search(r["description"] or ""))))
    # SoFi actuals: latest snapshot per month
    per_month = {}
    for d in sorted(balances):
        per_month[d[:7]] = balances[d]  # latest snapshot wins per month
    for m, snap in per_month.items():
        if m != month:
            continue
        col = MONTH_COL[m[5:]]
        chk = snap.get("SOFI-JointChecking")
        sav = snap.get("SOFI-JointSavings")
        if chk is not None:
            writes.append((ROW_SOFI_CHK, col, round(chk, 2)))
        if sav is not None:
            writes.append((ROW_SOFI_SAV, col, round(sav, 2)))
        if chk is not None and sav is not None:
            writes.append((ROW_SOFI_TOT, col, round(chk + sav, 2)))

    # ---- Data tab (full rewrite) ----
    cats = sorted({r["category"] for r in rows if r["flow_type"] == "spending"})
    data_tab = [[f"Pipeline rollups, written by refresh_forecast_sheet.py; do not hand-edit. Source: CashFlow/all_transactions.csv + balances.json, written at the {month} close."],
                ["Spending by category ($/mo, flow_type=spending)"], ["Category"] + months]
    for c in cats:
        tag = " (excluded from personal total)" if c in EXCLUDED_CATEGORIES else ""
        data_tab.append([c + tag] + [spend(m, lambda r, c=c: r["category"] == c) for m in months])
    data_tab.append(["Personal spend total (Monthly row 51 basis)"]
                    + [spend(m, lambda r: r["category"] not in EXCLUDED_CATEGORIES) for m in months])
    data_tab.append([])
    data_tab.append(["Income ($/mo, flow_type=income)"])
    data_tab.append(["Total income"] + [income(m, lambda r: True) for m in months])
    data_tab.append(["Maria income (desc: AUGER INC / Carbon Direct)"]
                    + [income(m, lambda r: MARIA_INCOME.search(r["description"] or "")) for m in months])
    data_tab.append(["Other income"]
                    + [income(m, lambda r: not MARIA_INCOME.search(r["description"] or "")) for m in months])
    data_tab.append([])
    data_tab.append(["Balance snapshots (balances.json)"])
    accts = sorted({a for d in balances.values() for a in d})
    data_tab.append(["Date"] + accts + ["SoFi total (checking+savings)"])
    for d in sorted(balances):
        sofi = sum(v for k, v in balances[d].items() if k.startswith("SOFI"))
        data_tab.append([d] + [balances[d].get(a, "") for a in accts] + [round(sofi, 2)])

    print(f"Monthly writes for {closed} ({len(writes)} cells):")
    for r, c, v in writes:
        print(f"  R{r}C{c} = {v}")
    if args.dry_run:
        print("dry run; nothing written")
        return

    import gspread
    from google.oauth2.credentials import Credentials
    gc = gspread.authorize(Credentials.from_authorized_user_file(str(TOKEN)))
    sh = gc.open_by_key(SHEET_ID)
    mon, data_ws = sh.worksheet("Monthly"), sh.worksheet("Data")

    mon.batch_update([{"range": gspread.utils.rowcol_to_a1(r, c), "values": [[v]]} for r, c, v in writes],
                     value_input_option="USER_ENTERED")
    # flip written cells to black (they're actuals now)
    sh.batch_update({"requests": [
        {"repeatCell": {"range": {"sheetId": mon.id, "startRowIndex": r - 1, "endRowIndex": r,
                                  "startColumnIndex": c - 1, "endColumnIndex": c},
                        "cell": {"userEnteredFormat": {"textFormat": {"foregroundColor": BLACK}}},
                        "fields": "userEnteredFormat.textFormat.foregroundColor"}}
        for r, c, _ in writes]})
    data_ws.clear()
    data_ws.update(range_name="A1", values=data_tab, value_input_option="USER_ENTERED")
    print(f"Wrote {len(writes)} Monthly cells + Data tab. "
          f"Check the yellow-flag items by hand: income rows other than Maria's, taxes, investments.")


if __name__ == "__main__":
    main()
