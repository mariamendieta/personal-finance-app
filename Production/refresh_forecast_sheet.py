"""Refresh the Woffieta Forecast Google Sheet from pipeline outputs.

Runs after cashflow.py in the monthly cycle (woffieta-data/CLAUDE.md "Adding a
month"). Writes ONLY the cells it owns, for ONE month (--month, default: last
complete month), and flips them to black per the actuals-black/forecast-gray
convention (woffieta-data/Forecast/requirements.md):

  - Monthly expense rows 4-48 via the RULES mapping below (mirrored on the
    Sheet's hidden Map tab), the Other row (52), and the pipeline total (53:
    all spending excl Luthien Expenses + Work Travel)
  - Monthly row 67: Maria's income (desc AUGER INC / CARBON DIRECT) and
    row 69: all other pipeline income (interest, Venmo, misc deposits)
  - Monthly rows 82-83: SoFi checking/savings history from balances.json.
    These rows hold FIRST-of-month balances (Scott also hand-enters them), so
    closing month M writes the snapshot nearest the M+1 month boundary
    (within 3 days) into the M+1 column, and only if that cell is empty —
    never clobbering a hand-entered balance. Row 84 is the =SUM(82:83)
    total formula on the Sheet; never write it.
  - Data tab: fully rewritten (category x month rollups, income, balances)

Invariant kept: rows 4-48 + Other == row 53 for every written month.
Single-month scope so it never silently overwrites earlier reconciled actuals.

Usage (gspread not in the app venv, so run via uv):
  uv run --with gspread python refresh_forecast_sheet.py [--data-dir PATH]
      [--month YYYY-MM] [--dry-run]

Portfolio balances (phase 2, done 2026-07-06, no script involvement): the
Forecast Sheet's own LIVE-Investments tab is the source of truth for
investment balances (the separate Asset Allocation Sheet is an archived
snapshot). Summary!D6 and Annual!C93/C96 are live formulas off that tab
(B69 retirement + B70 non-retirement-excl-SoFi, in $k) — do not overwrite
them from this script.
"""
import argparse, csv, json, re, sys
from pathlib import Path

SHEET_ID = "1ylY5nD6Tfo2KtGeb3s98_A4Qlh6DwgeBng6XnCayUmM"
TOKEN = Path.home() / ".config/mcp-gdrive/credentials-personal.json"
EXCLUDED_CATEGORIES = {"Luthien Expenses", "Work Travel", "Investments"}  # not personal spend
OTHER_ROW, TOTAL_ROW, MARIA_ROW, OTHER_INCOME_ROW = 52, 53, 67, 69
MARIA_INCOME = re.compile(r"AUGER INC|CARBON DIRECT", re.I)
ROW_SOFI_CHK, ROW_SOFI_SAV = 82, 83  # row 84 = SUM formula on the Sheet; row 86 = Other Liquidity Buckets — never write either
BLACK = {"red": 0, "green": 0, "blue": 0}

# (category, desc-regex or None=category default, Monthly row); first match wins.
# Mirror of the Sheet's Map tab — update both together.
RULES = [
    ("Taxes & Tax Fees", r"refund", 4),
    ("Taxes & Tax Fees", None, 5),
    ("Mortgage & Student Loans", r"firstmark", 9),
    ("Mortgage & Student Loans", None, 8),
    ("Car", r"jpmorgan|jp morgan", 12),
    ("Car", r"pemco", 13),
    ("Car", None, 41),
    ("Utilities", r"pemco", 13),
    ("Utilities", r"t-mobile|xfinity|comcast", 15),
    ("Utilities", r"seattleutil|city light|puget sound energy", 16),
    ("Utilities", r"southwest suburban", 18),
    ("Utilities", r"recology", 19),
    ("Childcare", r"lineleader", 22),
    ("Childcare", r"danna", 23),
    ("Childcare", r"city of burien|camp", 24),
    ("Childcare", r"worldkids|world kids", 25),
    ("Childcare", r"ymca", 34),
    ("Childcare", r"kami|music", 35),
    ("House & Maintenance", r"graciela", 29),
    ("House & Maintenance", r"iris|adriana", 30),  # row renamed "Iris + Adriana" 2026-07-06; covers Silvia Adriana Zelles
    ("House & Maintenance", r"israel", 31),
    ("House & Maintenance", r"francisco", 32),
    ("Fitness & Healthcare", None, 36),
    ("Therapy & Coaching", None, 37),
    ("Travel", r"delta|alaska|united|american air|avianca|latam|aeroplan|frontier|southwes|air canada", 39),
    ("Travel", None, 40),
    ("Restaurants", None, 43),
    ("Groceries", None, 44),
    ("Subscriptions", None, 45),
    ("Fees & Bank Charges", None, 46),
    ("Fun & Entertainment", None, 47),
    ("Shopping", None, 48),
]
LEAF_ROWS = [4, 5, 6, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26,
             29, 30, 31, 32, 34, 35, 36, 37, 39, 40, 41, 43, 44, 45, 46, 47, 48]
MONTH_COL = {m: c for c, m in enumerate(
    ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"], start=2)}


def classify(r):
    for cat, pat, row in RULES:
        if r["category"] == cat and (pat is None or re.search(pat, r["description"] or "", re.I)):
            return row
    return OTHER_ROW


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

    per = {row: 0.0 for row in LEAF_ROWS + [OTHER_ROW, TOTAL_ROW]}
    inc_maria = inc_other = 0.0
    for r in rows:
        if r["date"][:7] != month:
            continue
        if r["flow_type"] == "income":
            if MARIA_INCOME.search(r["description"] or ""):
                inc_maria += float(r["amount"])
            else:
                inc_other += float(r["amount"])
        if r["flow_type"] != "spending" or r["category"] in EXCLUDED_CATEGORIES:
            continue
        amt = -float(r["amount"])
        per[classify(r)] += amt
        per[TOTAL_ROW] += amt
    assert abs(sum(per[x] for x in LEAF_ROWS) + per[OTHER_ROW] - per[TOTAL_ROW]) < 0.01

    col = MONTH_COL[month[5:]]
    writes = [(row, col, round(per[row], 2)) for row in LEAF_ROWS + [OTHER_ROW, TOTAL_ROW]]
    writes.append((MARIA_ROW, col, round(inc_maria, 2)))
    writes.append((OTHER_INCOME_ROW, col, round(inc_other, 2)))

    # SoFi first-of-month balance: closing month M records the balance at the
    # M+1 boundary. Use the snapshot within 3 days of that boundary (if any),
    # target the M+1 column, and defer to any hand-entered value already there.
    from datetime import date, timedelta
    y, m = int(month[:4]), int(month[5:7])
    sofi_writes = []
    if m < 12:  # Dec close boundary is next year's Jan; no column for it
        boundary = date(y, m + 1, 1)
        bcol = MONTH_COL[f"{m + 1:02d}"]
        near = [d for d in balances
                if abs((date(*map(int, d.split("-"))) - boundary).days) <= 3]
        if near:
            snap = min(near, key=lambda d: abs((date(*map(int, d.split("-"))) - boundary).days))
            chk = balances[snap].get("SOFI-JointChecking")
            sav = balances[snap].get("SOFI-JointSavings")
            if chk is not None:
                sofi_writes.append((ROW_SOFI_CHK, bcol, round(chk, 2)))
            if sav is not None:
                sofi_writes.append((ROW_SOFI_SAV, bcol, round(sav, 2)))

    # ---- Data tab (full rewrite) ----
    def spend(m, pred):
        return round(sum(-float(r["amount"]) for r in rows
                         if r["date"][:7] == m and r["flow_type"] == "spending" and pred(r)), 2)

    def income(m, pred):
        return round(sum(float(r["amount"]) for r in rows
                         if r["date"][:7] == m and r["flow_type"] == "income" and pred(r)), 2)

    cats = sorted({r["category"] for r in rows if r["flow_type"] == "spending"})
    data_tab = [[f"Pipeline rollups, written by refresh_forecast_sheet.py; do not hand-edit. Source: CashFlow/all_transactions.csv + balances.json, written at the {month} close."],
                ["Spending by category ($/mo, flow_type=spending)"], ["Category"] + months]
    for c in cats:
        tag = " (excluded from personal total)" if c in EXCLUDED_CATEGORIES else ""
        data_tab.append([c + tag] + [spend(m, lambda r, c=c: r["category"] == c) for m in months])
    data_tab.append(["Personal spend total (Monthly row 53 basis)"]
                    + [spend(m, lambda r: r["category"] not in EXCLUDED_CATEGORIES) for m in months])
    data_tab.append([])
    data_tab.append(["Income ($/mo, flow_type=income)"])
    data_tab.append(["Total income"] + [income(m, lambda r: True) for m in months])
    data_tab.append([])
    data_tab.append(["Balance snapshots (balances.json)"])
    accts = sorted({a for d in balances.values() for a in d})
    data_tab.append(["Date"] + accts + ["SoFi total (checking+savings)"])
    for d in sorted(balances):
        sofi = sum(v for k, v in balances[d].items() if k.startswith("SOFI"))
        data_tab.append([d] + [balances[d].get(a, "") for a in accts] + [round(sofi, 2)])

    print(f"Monthly writes for {month} ({len(writes)} cells):")
    for r, c, v in writes:
        print(f"  R{r}C{c} = {v}")
    for r, c, v in sofi_writes:
        print(f"  R{r}C{c} = {v} (SoFi first-of-month, skipped if hand-entered)")
    if args.dry_run:
        print("dry run; nothing written")
        return

    import gspread
    from google.oauth2.credentials import Credentials
    gc = gspread.authorize(Credentials.from_authorized_user_file(str(TOKEN)))
    sh = gc.open_by_key(SHEET_ID)
    mon, data_ws = sh.worksheet("Monthly"), sh.worksheet("Data")

    for r, c, v in sofi_writes:
        existing = mon.cell(r, c).value
        if existing in (None, ""):
            writes.append((r, c, v))
        else:
            print(f"  R{r}C{c}: kept hand-entered {existing}, skipped {v}")

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
    print(f"Wrote {len(writes)} Monthly cells + Data tab. Hand-check afterward: "
          f"Scott income (row 64), reimbursements (65), gifts (70), investments (59-61).")


if __name__ == "__main__":
    main()
