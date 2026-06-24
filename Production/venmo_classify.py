"""
Venmo statement classifier — Woffieta family finances.

Reads raw Venmo exports (VenmoStatement_*.csv) and classifies each payment as
Luthien-reimbursable (Scott's business) vs Personal, using the Note memo and
recipient. Venmo's export has clean memos ("Week of 3/23 7h32m", "Uber Luthien
expense"), so this auto-tags contractors and business expenses that otherwise
land in the generic SoFi "VENMO" / Unclassified bucket.

This is a STANDALONE report. It does NOT merge into the cashflow totals:
Scott's Venmo top-ups are funded from SoFi (Bancorp *7341), so the dollars
already appear as "VENMO" debits in the SoFi data. Merging would double-count.
Use this to see the Luthien-vs-personal split and to inform manual
reclassification of the SoFi VENMO charges.

Usage:
    uv run --with pandas python venmo_classify.py          # default dir
    VENMO_DIR=/path/to/venmo uv run python venmo_classify.py

Default input dir: $VENMO_DIR, else ~/build/woffieta-data/data-sources/venmo
Writes venmo_classified.csv (per-transaction) into that dir.
"""

import csv
import glob
import os
import re
from pathlib import Path

VENMO_DIR = Path(
    os.environ.get("VENMO_DIR", "~/build/woffieta-data/data-sources/venmo")
).expanduser()

# A payment is Luthien-reimbursable if the memo matches. We classify on the memo
# (not recipient names) so no personal names live in this public repo; Scott's
# contractor memos are clean ("Week of 3/23 7h32m", "Uber Luthien expense").
# If a future payment has a vague memo it falls to Personal — fix the memo, or
# add it to venmo_classified.csv review.
LUTHIEN_MEMO = re.compile(
    r"luthien|week of|design help|\bQA\b|\bbug\b|\d+\s*h(ou)?rs?\b|hours?\s+\d+\s*min",
    re.I,
)


def classify(note: str, counterparty: str) -> str:
    if LUTHIEN_MEMO.search(note or ""):
        return "Luthien"
    return "Personal"


def parse_amount(raw: str) -> float:
    """Venmo amounts look like '- $376.00' (out) or '+ $40.00' / '$40.00' (in)."""
    s = (raw or "").replace("$", "").replace(",", "").replace(" ", "")
    if not s or s in ("-", "+"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_file(path: Path) -> list[dict]:
    rows = list(csv.reader(open(path)))
    # The real header is the row containing both 'Datetime' and 'Note'.
    header_i = next(
        (i for i, r in enumerate(rows) if "Datetime" in r and "Note" in r), None
    )
    if header_i is None:
        return []
    header = rows[header_i]
    col = {name: header.index(name) for name in header if name}
    out = []
    for r in rows[header_i + 1:]:
        if len(r) <= col.get("Amount (total)", 999):
            continue
        if not r[col["ID"]].strip():  # skip balance / disclaimer rows
            continue
        amt = parse_amount(r[col["Amount (total)"]])
        if amt == 0.0:
            continue
        frm, to = r[col["From"]], r[col["To"]]
        note = r[col["Note"]].replace("\n", " ").strip()
        direction = "out" if amt < 0 else "in"
        counterparty = to if direction == "out" else frm
        out.append(
            {
                "date": r[col["Datetime"]][:10],
                "direction": direction,
                "counterparty": counterparty,
                "amount": abs(amt),
                "bucket": classify(note, counterparty) if direction == "out" else "Personal",
                "note": note,
                "funding": r[col.get("Funding Source", 0)] if "Funding Source" in col else "",
                "source_file": path.name,
            }
        )
    return out


def main() -> None:
    files = sorted(glob.glob(str(VENMO_DIR / "VenmoStatement_*.csv")))
    if not files:
        print(f"No VenmoStatement_*.csv found in {VENMO_DIR}")
        return
    txns: list[dict] = []
    for f in files:
        txns.extend(parse_file(Path(f)))

    out_txns = [t for t in txns if t["direction"] == "out"]
    luthien = sum(t["amount"] for t in out_txns if t["bucket"] == "Luthien")
    personal = sum(t["amount"] for t in out_txns if t["bucket"] == "Personal")

    print(f"Parsed {len(txns)} Venmo transactions from {len(files)} file(s).\n")
    print("Outgoing (Scott -> others):")
    print(f"  Luthien-reimbursable: ${luthien:,.2f}")
    print(f"  Personal:             ${personal:,.2f}\n")

    # By month x bucket
    by_month: dict[str, dict[str, float]] = {}
    for t in out_txns:
        m = t["date"][:7]
        by_month.setdefault(m, {"Luthien": 0.0, "Personal": 0.0})[t["bucket"]] += t["amount"]
    print(f"{'Month':9} {'Luthien':>12} {'Personal':>12}")
    for m in sorted(by_month):
        b = by_month[m]
        print(f"{m:9} {b['Luthien']:>12,.2f} {b['Personal']:>12,.2f}")

    print("\nLuthien-tagged payments:")
    for t in sorted((t for t in out_txns if t["bucket"] == "Luthien"), key=lambda t: t["date"]):
        print(f"  {t['date']}  ${t['amount']:>8,.2f}  {t['counterparty'][:20]:20}  {t['note'][:45]}")

    # Write per-transaction classification
    out_path = VENMO_DIR / "venmo_classified.csv"
    with open(out_path, "w", newline="") as fh:
        w = csv.DictWriter(
            fh,
            fieldnames=["date", "direction", "counterparty", "amount", "bucket", "note", "funding", "source_file"],
        )
        w.writeheader()
        w.writerows(sorted(txns, key=lambda t: t["date"]))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
