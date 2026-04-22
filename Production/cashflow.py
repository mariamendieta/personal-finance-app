"""
Cash Flow Compiler — Mendieta-Umana Family Finances

Reads all checking, savings, and credit card CSV exports from:
    Data/CashFlow/<MonthYY>/Credit Cards/*.csv
    Data/CashFlow/<MonthYY>/Checking and Savings/*.csv

Normalizes every transaction into a unified schema and tags each one
with a flow_type so credit card payments and internal transfers are
never double-counted in spending analysis.

flow_type values:
    spending          — real purchase or bill (count this for cash flow)
    income            — paycheck, deposit, interest, reimbursement
    cc_payment        — credit card payment (shows on BOTH sides; exclude both)
    internal_transfer — movement between own accounts (exclude)
    other             — fees, uncategorized (review manually)
"""

import os
import re
import pandas as pd
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────

DATA_ROOT = Path(__file__).parent / "CashFlow"
OUTPUT_FILE = Path(__file__).parent / "CashFlow" / "all_transactions.csv"

# ── Parsers for each CSV format ────────────────────────────────────────────

def parse_chase_card(filepath: Path, account_name: str) -> pd.DataFrame:
    """Chase-issued cards: Aeroplan, AmazonPrime.
    Columns: Transaction Date, Post Date, Description, Category, Type, Amount, Memo
    Amount is negative for purchases, positive for payments.
    """
    df = pd.read_csv(filepath)
    rows = []
    for _, r in df.iterrows():
        amount_raw = r.get("Amount", 0)
        amount = float(amount_raw) if pd.notna(amount_raw) else 0.0
        tx_type = str(r.get("Type", "")).strip()
        rows.append({
            "date": pd.to_datetime(r["Transaction Date"], format="mixed"),
            "post_date": pd.to_datetime(r["Post Date"], format="mixed"),
            "description": str(r["Description"]).strip(),
            "original_category": str(r.get("Category", "")).strip(),
            "amount": amount,
            "account": account_name,
            "account_type": "credit_card",
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_capital_one(filepath: Path, account_name: str) -> pd.DataFrame:
    """Capital One VentureX.
    Columns: Transaction Date, Posted Date, Card No., Description, Category, Debit, Credit
    Debit = purchase amount (positive number), Credit = payment/refund (positive number).
    """
    df = pd.read_csv(filepath)
    rows = []
    for _, r in df.iterrows():
        debit = float(r["Debit"]) if pd.notna(r.get("Debit")) else 0.0
        credit = float(r["Credit"]) if pd.notna(r.get("Credit")) else 0.0
        # Normalize: purchases negative, payments/credits positive
        amount = credit - debit
        rows.append({
            "date": pd.to_datetime(r["Transaction Date"]),
            "post_date": pd.to_datetime(r["Posted Date"]),
            "description": str(r["Description"]).strip(),
            "original_category": str(r.get("Category", "")).strip(),
            "amount": amount,
            "account": account_name,
            "account_type": "credit_card",
            "source_file": filepath.name,
            "card_last4": str(r.get("Card No.", "")).strip().zfill(4) if pd.notna(r.get("Card No.")) else "",
        })
    return pd.DataFrame(rows)


def parse_alaska_card(filepath: Path, account_name: str) -> pd.DataFrame:
    """Alaska Airlines BofA card.
    Columns: Posted Date, Reference Number, Payee, Address, Amount
    Amount is negative for purchases, positive for payments.
    """
    df = pd.read_csv(filepath)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": pd.to_datetime(r["Posted Date"], format="mixed"),
            "post_date": pd.to_datetime(r["Posted Date"], format="mixed"),
            "description": str(r["Payee"]).strip(),
            "original_category": "",
            "amount": float(r["Amount"]),
            "account": account_name,
            "account_type": "credit_card",
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_barclays_card(filepath: Path, account_name: str) -> pd.DataFrame:
    """Barclays credit card.
    Has a header section, then: Transaction Date, Description, Category, Amount
    Amount is negative for purchases, positive for payments.
    """
    with open(filepath, "r") as f:
        lines = f.readlines()
    tx_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Transaction Date,Description"):
            tx_start = i
            break
    if tx_start is None:
        return pd.DataFrame()
    from io import StringIO
    csv_text = "".join(lines[tx_start:])
    df = pd.read_csv(StringIO(csv_text))
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": pd.to_datetime(r["Transaction Date"]),
            "post_date": pd.to_datetime(r["Transaction Date"]),
            "description": str(r["Description"]).strip(),
            "original_category": str(r.get("Category", "")).strip(),
            "amount": float(r["Amount"]),
            "account": account_name,
            "account_type": "credit_card",
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_citi_card(filepath: Path, account_name: str) -> pd.DataFrame:
    """Citi credit card (AAdvantage).
    Columns: Status, Date, Description, Debit, Credit, Member Name
    Debit = purchases, Credit = payments/refunds (may be negative values).
    """
    df = pd.read_csv(filepath)
    rows = []
    for _, r in df.iterrows():
        debit = abs(float(r["Debit"])) if pd.notna(r.get("Debit")) else 0.0
        credit = abs(float(r["Credit"])) if pd.notna(r.get("Credit")) else 0.0
        amount = credit - debit
        desc = str(r["Description"]).strip().strip('"')
        rows.append({
            "date": pd.to_datetime(r["Date"]),
            "post_date": pd.to_datetime(r["Date"]),
            "description": desc,
            "original_category": "",
            "amount": amount,
            "account": account_name,
            "account_type": "credit_card",
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_sofi(filepath: Path, account_name: str) -> pd.DataFrame:
    """SoFi checking or savings.
    Columns: Date, Description, Type, Amount, Current balance, Status
    """
    df = pd.read_csv(filepath)
    # Skip rows with no transactions
    if df.empty or "Date" not in df.columns:
        return pd.DataFrame()

    account_type = "savings" if "saving" in account_name.lower() else "checking"
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": pd.to_datetime(r["Date"]),
            "post_date": pd.to_datetime(r["Date"]),
            "description": str(r["Description"]).strip(),
            "original_category": str(r.get("Type", "")).strip(),
            "amount": float(r["Amount"]),
            "account": account_name,
            "account_type": account_type,
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_boa_bank(filepath: Path, account_name: str) -> pd.DataFrame:
    """Bank of America checking or savings.
    Has a summary header section, then a transaction table starting with
    Date,Description,Amount,Running Bal.
    """
    # Read raw lines and find the transaction table
    with open(filepath, "r") as f:
        lines = f.readlines()

    # Find the header row for the transaction table
    tx_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("Date,Description,Amount"):
            tx_start = i
            break

    if tx_start is None:
        return pd.DataFrame()

    # Filter to only data rows (skip "Beginning balance" rows)
    from io import StringIO
    tx_text = "".join(lines[tx_start:])
    df = pd.read_csv(StringIO(tx_text))

    account_type = "savings" if "saving" in account_name.lower() else "checking"
    rows = []
    for _, r in df.iterrows():
        desc = str(r["Description"]).strip()
        if "Beginning balance" in desc:
            continue
        amount_str = str(r["Amount"]).replace(",", "")
        try:
            amount = float(amount_str)
        except ValueError:
            continue
        rows.append({
            "date": pd.to_datetime(r["Date"], format="mixed"),
            "post_date": pd.to_datetime(r["Date"], format="mixed"),
            "description": desc,
            "original_category": "",
            "amount": amount,
            "account": account_name,
            "account_type": account_type,
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_chase_checking(filepath: Path, account_name: str) -> pd.DataFrame:
    """Chase checking account.
    Columns: Details, Posting Date, Description, Amount, Type, Balance, Check or Slip #
    Note: CSV has trailing commas creating an extra column, so we use index_col=False.
    """
    df = pd.read_csv(filepath, index_col=False)
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "date": pd.to_datetime(r["Posting Date"], format="mixed"),
            "post_date": pd.to_datetime(r["Posting Date"], format="mixed"),
            "description": str(r["Description"]).strip(),
            "original_category": str(r.get("Type", "")).strip(),
            "amount": float(r["Amount"]),
            "account": account_name,
            "account_type": "checking",
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


def parse_generic(filepath: Path, account_name: str) -> pd.DataFrame:
    """Generic CSV parser that auto-detects columns by header names.

    Tries to match known parser patterns first, then falls back to
    heuristic column detection for date, description, and amount fields.
    """
    # Try reading with and without index_col=False (handles trailing commas)
    try:
        df = pd.read_csv(filepath, index_col=False)
    except Exception:
        df = pd.read_csv(filepath)

    if df.empty:
        return pd.DataFrame()

    cols = set(c.strip() for c in df.columns)

    # ── Try matching known parser patterns by headers ──

    # Chase card pattern: Post Date, Description, Amount, Category
    if {"Post Date", "Description", "Amount", "Category"}.issubset(cols):
        return parse_chase_card(filepath, account_name)

    # Capital One pattern: Transaction Date, Posted Date, Debit, Credit
    if {"Transaction Date", "Posted Date", "Debit", "Credit"}.issubset(cols):
        return parse_capital_one(filepath, account_name)

    # Alaska/BoA card pattern: Posted Date, Payee, Amount
    if {"Posted Date", "Payee", "Amount"}.issubset(cols):
        return parse_alaska_card(filepath, account_name)

    # Citi card pattern: Status, Date, Description, Debit, Credit, Member Name
    if {"Status", "Date", "Description", "Debit", "Credit", "Member Name"}.issubset(cols):
        return parse_citi_card(filepath, account_name)

    # SoFi pattern: Date, Description, Amount, and (Current balance or Status)
    if {"Date", "Description", "Amount"}.issubset(cols) and (
        "Current balance" in cols or "Status" in cols
    ):
        return parse_sofi(filepath, account_name)

    # Chase checking pattern: Details, Posting Date, Description, Balance
    if {"Details", "Posting Date", "Description", "Balance"}.issubset(cols):
        return parse_chase_checking(filepath, account_name)

    # ── Generic fallback: detect columns heuristically ──

    # Find date column
    date_candidates = [
        "Date", "Transaction Date", "Posted Date", "Posting Date",
        "Post Date", "Trans Date", "Txn Date",
    ]
    date_col = None
    for candidate in date_candidates:
        if candidate in cols:
            date_col = candidate
            break
    # Case-insensitive fallback
    if date_col is None:
        cols_lower = {c.lower(): c for c in df.columns}
        for candidate in date_candidates:
            if candidate.lower() in cols_lower:
                date_col = cols_lower[candidate.lower()]
                break

    if date_col is None:
        print(f"  ⚠ Generic parser: no date column found in {filepath.name}")
        return pd.DataFrame()

    # Find description column
    desc_candidates = [
        "Description", "Payee", "Merchant", "Name", "Memo",
        "Transaction Description", "Merchant Name",
    ]
    desc_col = None
    for candidate in desc_candidates:
        if candidate in cols:
            desc_col = candidate
            break
    if desc_col is None:
        cols_lower = {c.lower(): c for c in df.columns}
        for candidate in desc_candidates:
            if candidate.lower() in cols_lower:
                desc_col = cols_lower[candidate.lower()]
                break

    if desc_col is None:
        print(f"  ⚠ Generic parser: no description column found in {filepath.name}")
        return pd.DataFrame()

    # Find amount column(s)
    has_debit_credit = "Debit" in cols and "Credit" in cols
    if not has_debit_credit:
        cols_lower_map = {c.lower(): c for c in df.columns}
        has_debit_credit = "debit" in cols_lower_map and "credit" in cols_lower_map

    amount_col = None
    if not has_debit_credit:
        amount_candidates = ["Amount", "Value", "Transaction Amount"]
        for candidate in amount_candidates:
            if candidate in cols:
                amount_col = candidate
                break
        if amount_col is None:
            cols_lower = {c.lower(): c for c in df.columns}
            for candidate in amount_candidates:
                if candidate.lower() in cols_lower:
                    amount_col = cols_lower[candidate.lower()]
                    break

    if amount_col is None and not has_debit_credit:
        print(f"  ⚠ Generic parser: no amount column found in {filepath.name}")
        return pd.DataFrame()

    # Find category column (optional)
    cat_col = None
    cat_candidates = ["Category", "Type", "Transaction Type"]
    for candidate in cat_candidates:
        if candidate in cols:
            cat_col = candidate
            break

    # Guess account type from name
    name_lower = account_name.lower()
    if any(kw in name_lower for kw in ["checking", "savings", "saving", "bank"]):
        account_type = "savings" if "saving" in name_lower else "checking"
    else:
        account_type = "credit_card"

    # Find debit/credit columns (case-insensitive)
    debit_col = None
    credit_col = None
    if has_debit_credit:
        for c in df.columns:
            if c.strip().lower() == "debit":
                debit_col = c
            elif c.strip().lower() == "credit":
                credit_col = c

    rows = []
    for _, r in df.iterrows():
        # Parse amount
        if has_debit_credit and debit_col and credit_col:
            debit = float(r[debit_col]) if pd.notna(r.get(debit_col)) else 0.0
            credit = float(r[credit_col]) if pd.notna(r.get(credit_col)) else 0.0
            amount = credit - debit
        else:
            raw = r.get(amount_col, 0)
            try:
                amount = float(str(raw).replace(",", "")) if pd.notna(raw) else 0.0
            except (ValueError, TypeError):
                continue

        # Parse date
        try:
            parsed_date = pd.to_datetime(r[date_col], format="mixed")
        except Exception:
            continue

        desc = str(r.get(desc_col, "")).strip()
        orig_cat = str(r.get(cat_col, "")).strip() if cat_col else ""

        rows.append({
            "date": parsed_date,
            "post_date": parsed_date,
            "description": desc,
            "original_category": orig_cat,
            "amount": amount,
            "account": account_name,
            "account_type": account_type,
            "source_file": filepath.name,
        })
    return pd.DataFrame(rows)


# ── File-to-parser routing ────────────────────────────────────────────────

def _account_name_from_filename(filepath: Path) -> str:
    """Derive a human-readable account name from a filename."""
    stem = filepath.stem
    # Remove common suffixes like _Mar26, _2026, etc.
    stem = re.sub(r"[_-]\w{3}\d{2}$", "", stem)
    stem = re.sub(r"[_-]\d{4}$", "", stem)
    return stem.replace("_", " ").replace("-", " ").title()


def detect_parser(filepath: Path):
    """Return (parser_function, account_name) based on filename."""
    name = filepath.stem.lower()

    if "aeroplan" in name:
        return parse_chase_card, "Aeroplan"
    elif "amazonprime" in name:
        return parse_chase_card, "AmazonPrime"
    elif "united" in name:
        return parse_chase_card, "United"
    elif "venturex" in name:
        return parse_capital_one, "VentureX"
    elif "ventureone" in name:
        return parse_capital_one, "VentureOne"
    elif "scott" in name and "alaska" in name:
        return parse_alaska_card, "Alaska-Scott"
    elif "cash-rewards" in name or "cashrewards" in name:
        return parse_alaska_card, "CashRewards-Scott"
    elif "_3728" in name:
        return parse_alaska_card, "Alaska-Scott"
    elif "_2382" in name:
        return parse_alaska_card, "CashRewards-Scott"
    elif "alaska" in name:
        return parse_alaska_card, "Alaska"
    elif "citi" in name or "aadvantage" in name:
        return parse_citi_card, "CitiAAdvantage"
    elif "barclay" in name:
        return parse_barclays_card, "Barclays"
    elif "chasechecking" in name:
        return parse_chase_checking, "Chase-Checking"
    elif "sofi" in name and "checking" in name:
        return parse_sofi, "SoFi-JointChecking"
    elif "sofi" in name and "saving" in name:
        return parse_sofi, "SoFi-JointSavings"
    elif "boa" in name and "checking" in name:
        return parse_boa_bank, "BoA-Checking"
    elif "boa" in name and "saving" in name:
        return parse_boa_bank, "BoA-Savings"
    else:
        # Fallback: try generic auto-detect parser
        account_name = _account_name_from_filename(filepath)
        return parse_generic, account_name


# ── Flow-type classification ──────────────────────────────────────────────

# Patterns that indicate a credit card payment (on the checking/savings side)
CC_PAYMENT_PATTERNS = re.compile(
    r"CAPITAL ONE|CHASE CREDIT CRD|BANK OF AMERICA(?!, N\.A\.)|"
    r"AUTOMATIC PAYMENT - THANK|AUTOPAY PYMT|"
    r"PAYMENT - THANK YOU|BA ELECTRONIC PAYMENT|"
    r"CITI AUTOPAY|BARCLAYCARD|CREDIT-TRAVEL REWARD|AUTOPAY.*AUTO-PMT|Payment Received",
    re.IGNORECASE,
)

# Patterns for internal transfers between own accounts
INTERNAL_TRANSFER_PATTERNS = re.compile(
    r"From Savings|To Checking|From Checking|To Savings|"
    r"SoFi Bank DES:TRANSFER|BANK OF AMERICA, N\.A\.|"
    r"Online Transfer.*from SoFi|Online Transfer.*to SoFi|Online Transfer from SAV|"
    r"Online Banking transfer|"
    r"SoFi Bank\s+TRANSFER|Manual DB-Bkrg|Manual CR-Bkrg|"
    r"JPMORGAN CHASE BANK, NA|"
    r"ACCT_XFER|CHARLES SCHWAB BANK",
    re.IGNORECASE,
)

# Income patterns
INCOME_PATTERNS = re.compile(
    r"DIRECT_DEPOSIT|CHECK_DEPOSIT|CARBON DIRECT IN|Interest earned|"
    r"INTEREST_EARNED|INTEREST PAYMENT|WIRE_INCOMING|CHIPS CREDIT|"
    r"Cash Redemption|Aseltine.*Settlement|BKOFAMERICA ATM.*DEPOSIT|Seattle Network|"
    r"Epoch Artificial|Zelle.*from|CREDIT-TRAVEL REWARD",
    re.IGNORECASE,
)


def classify_flow_type(row: pd.Series) -> str:
    """Classify a transaction into a flow_type."""
    desc = str(row["description"])
    cat = str(row.get("original_category", ""))
    acct_type = row["account_type"]
    amount = row["amount"]

    # ── Annual/member fees on credit cards are spending, not cc_payment ──
    if re.search(r"MEMBER FEE", desc, re.I) and amount < 0:
        return "spending"

    # ── Credit card rewards (before cc_payment check) ──
    if re.search(r"CREDIT-TRAVEL REWARD", desc, re.I):
        return "income"

    # ── Credit card side: payments received ──
    if acct_type == "credit_card":
        if CC_PAYMENT_PATTERNS.search(desc):
            return "cc_payment"

    # ── Bank side: payments to credit cards ──
    if acct_type in ("checking", "savings"):
        if CC_PAYMENT_PATTERNS.search(desc):
            return "cc_payment"

    # ── Income (check before internal transfers so CHIPS CREDIT isn't masked) ──
    if INCOME_PATTERNS.search(desc) or INCOME_PATTERNS.search(cat):
        return "income"

    # ── Investment transfers (before internal_transfer check) ──
    # Money going TO brokerage = spending (investment)
    if re.search(r"Manual DB-Bkrg|CHARLES SCHWAB BANK", desc, re.I) and amount < 0:
        return "spending"
    # Money coming FROM brokerage = income (withdrawal)
    if re.search(r"Manual CR-Bkrg|SOFI SECURITIES", desc, re.I) and amount > 0:
        return "income"

    # ── Internal transfers ──
    if INTERNAL_TRANSFER_PATTERNS.search(desc):
        return "internal_transfer"

    # Venmo deposits into bank = income (reimbursements, payments received)
    if re.search(r"^VENMO$", desc, re.I) and amount > 0:
        return "income"

    # JPMorgan Chase from savings — keep as spending (double lease payments are real)

    # SoFi OTHER type with no other match is often an auto-cover transfer
    if cat == "OTHER" and acct_type in ("checking", "savings"):
        if not re.search(r"Miscellaneous Debit|Wire Transfer", desc, re.I):
            return "internal_transfer"

    # ── Spending ──
    # Credit card charges (negative on Chase/Amazon, negative debit-credit on CapOne)
    if acct_type == "credit_card" and amount < 0:
        return "spending"
    # Credit card refunds
    if acct_type == "credit_card" and amount > 0:
        return "other"  # refunds — review individually

    # Bank debits that aren't cc payments or transfers = real spending
    if acct_type in ("checking", "savings") and amount < 0:
        return "spending"

    return "other"


# ── Spending category classification ──────────────────────────────────────
#
# Categories from Context.md, with "Unclassified" split into
# subcategories for more granular analysis.
#
# Fixed Obligations:
#   Mortgage & Student Loans, Car, Utilities, Childcare, Taxes & Tax Fees
# Variable Expenses:
#   House & Maintenance, Fitness & Healthcare, Travel,
#   Groceries, Restaurants, Subscriptions, Shopping, Fun & Entertainment, Pets
# Non-spending:
#   Income, CC Payment, Internal Transfer, Fees & Other

# Order matters — first match wins. Each entry is (pattern, category).
CATEGORY_RULES: list[tuple[re.Pattern, str]] = [
    # ── Investments (401k, IRA, brokerage) ──
    (re.compile(r"SOFI SECURITIES|VANGUARD BUY|VANGUARD|Manual DB-Bkrg|Manual CR-Bkrg|CHARLES SCHWAB", re.I), "Investments"),

    # ── Mortgage & Student Loans ──
    (re.compile(r"Firstmark|Common Bond|MOHELA", re.I), "Mortgage & Student Loans"),

    # ── Car ──
    (re.compile(r"SAFEWAY FUEL|76\s*-\s|WSDOT-GOODTOGO|PayMyNotice|"
                r"SDOT PAYBYPHONE|CTLP\*CSC SERVICEWORKS|Gas/Automotive|"
                r"PIKE PLACE MARKET PDA|WA STATE DOL|WA DOL LIC|"
                r"SPOTHERO|DIAMOND PARKING|HONK PARKING|ParkWhiz|"
                r"TESLA SUPERCHARGER|CHARGEPOINT|SPNW Seattle Citations", re.I), "Car"),

    # ── Utilities ──
    (re.compile(r"T-MOBILE PARK", re.I), "Fun & Entertainment"),
    (re.compile(r"T-MOBILE|TMOBILE|SEATTLEUTILTIES|SOUTHWEST SUBURBAN|"
                r"RECOLOGY|Seattle City Light|SPU|COMCAST|XFINITY", re.I), "Utilities"),
    (re.compile(r"PEMCO MUTUAL|PEMCO Mutual", re.I), "Utilities"),  # car + umbrella insurance (home insurance is with mortgage)

    # ── Childcare ──
    (re.compile(r"WORLDKIDS|LINELEADER|RightAtSchool", re.I), "Childcare"),
    (re.compile(r"Zelle.*Danna", re.I), "Childcare"),  # Danna = Spanish tutor
    (re.compile(r"MY SPANISH NANNY|LITTLE SPOON|SCHOOL OF ROCK|PRESCHOOL SMILES", re.I), "Childcare"),
    (re.compile(r"SP WOOM BIKES", re.I), "Childcare"),  # kids bikes

    # ── House & Maintenance ──
    (re.compile(r"Zelle.*Graciela", re.I), "House & Maintenance"),  # cleaning
    (re.compile(r"Zelle.*Iris", re.I), "House & Maintenance"),      # house helper
    (re.compile(r"Zelle.*Silvia.*Diaz|Zelle.*Silvia Adriana", re.I), "House & Maintenance"),  # former house helper
    (re.compile(r"Zelle.*Israel", re.I), "House & Maintenance"),     # yard
    (re.compile(r"Zelle.*Francisco", re.I), "House & Maintenance"),  # contractor
    (re.compile(r"ECOSHIELD PEST|NUTONE DRY CLEANERS", re.I), "House & Maintenance"),

    # ── Fitness & Healthcare ──
    (re.compile(r"PUGET SOUND BASKETBALL", re.I), "Fitness & Healthcare"),
    (re.compile(r"DENTIST|Amazon Pharmacy|THERAPIST|Health Care|A\.Z\. Pharmacy|DENTIS", re.I), "Fitness & Healthcare"),
    (re.compile(r"PROVIDENCE|BLVD.*RUDY|PAULINE.S NAIL SPA|CLAUDIA PRIETO", re.I), "Fitness & Healthcare"),
    (re.compile(r"PAYPAL \*SEATAC BMX|PP\*SURF BALLARD", re.I), "Fitness & Healthcare"),

    # ── Childcare (YMCA = kids programs) ──
    (re.compile(r"YMCA", re.I), "Childcare"),

    # ── Luthien Expenses ──
    (re.compile(r"UPWORK|LUTHIEN RESEARCH", re.I), "Luthien Expenses"),

    # ── Therapy & Coaching ──
    (re.compile(r"MARGARITA QUIJANO|HOTMART|BEAUTIFUL\.AI|GAMRAY", re.I), "Therapy & Coaching"),  # therapist + coaching courses
    # Standalone PAYPAL (coaching) is handled in classify_category

    # ── Travel ──
    (re.compile(r"ALASKA AIR|UNITED\s|DELTA AIR|FRONTIER AI|COT\*FLT|"
                r"Airfare|EXPEDIA|AIR CAN\*", re.I), "Travel"),
    (re.compile(r"UKVI ETAM|CRYSTAL INNTOPIA|CRYSTAL MTN|CRYSTAL.*ENUMCLAW|"
                r"FIRESIDE CAFE CRYSTAL|BREW 62 ENUMCLAW", re.I), "Travel"),
    (re.compile(r"AIRBNB|GUESTRS|VIDANTA|ROYAL SOLARIS|EXPERIENCIAS XCARET|"
                r"Lodging|RMTLY\*|REMITLY|NEXION|TURO", re.I), "Travel"),
    (re.compile(r"UBER\s+\*TRIP|LYFT\s+\*RIDE|LYFT\s+\*\d|CLIPPER TRANSIT|ORCA\b|"
                r"MERPAGO\*TRANSPORTE|MERPAGO\*UBALDO|MERPAGO\*TOURSELSI|"
                r"MTA\*NYCT|TFL TRAVEL|CITIBIK|EMPRESA MALAGUENA|"
                r"WSFERRIES|MARTA TVM|CARCAMOVIL", re.I), "Travel"),
    (re.compile(r"WIFIONBOARD|BA INFLIGHT|"
                r"Chairs/Carts|Nyx\*SmarteCarte|SmarteCarte|NYX\*PGGroup|"
                r"Goldcar|TIDES OF ANACORTES|ACE OF ANACORTES", re.I), "Travel"),
    (re.compile(r"CANCUN PL SOLARIS|OXXO YALMAKAN|ASUR C CONV SHOP|"
                r"LOS CINCO SOLES|SUNSET NEWS ST|HUDSONNEWS|"
                r"HUDSON ST\s?\d|1866_YYZ|ADRENALINE ST|DFWTEXASMONTHLYST|"
                r"NEWREST TRAVEL|KANGRA AIRPORT|MPOS-AVIANCA|"
                r"PPOINT_\*NR97|CHOOOSE|"
                r"SBIJAIPUR|SBISBI|SBINEAR|SBISIDE|SBISIDHBARI|STATE BANK OF INDIA", re.I), "Travel"),

    # ── Groceries ──
    (re.compile(r"COSTCO|INSTACART|IC\*|SAFEWAY(?! FUEL)|WHOLEFDS|"
                r"NEW STAR MARKET|Groceries|PCC -|QFC|TRADER JOE|"
                r"ALDI |SUPER DELI MART|4 CORNERS MARKETPLACE|"
                r"E AND R NATURAL FOOD|RAINBOW MINI MART|ORGANIC LIFE START", re.I), "Groceries"),

    # ── Restaurants ──
    (re.compile(r"UBER\s+\*EATS|GRUBHUB|DD \*|DLO\*RAPPI|Rappi(?! Bogota)", re.I), "Restaurants"),
    (re.compile(r"Rappi Bogota", re.I), "Restaurants"),
    (re.compile(r"Zelle.*Katherine.*Pierson", re.I), "Restaurants"),
    (re.compile(r"SUBWAY|CHICK-FIL-A|CHIPOTLE|ALADDIN GYRO|SAIGON DELI|"
                r"PIZZA ZONE|COLDSTONE|SNACK\*|LAZY DOG RESTAURANT|EATS ON 57|"
                r"TROPICALIA|OHANA MARBELLA|KUDEDON|HOJAS|"
                r"MEAL TRAIN|STK DENVER|EMERALD CITY SMOOTHIE|MARKETIME FOODS|"
                r"JACK IN THE BOX|POTBELLY|CASABLANCA EXPRESS|"
                r"SHACK N STACK|TAQUERIA EL RINCON|7-ELEVEN", re.I), "Restaurants"),
    (re.compile(r"TST\*|SQ \*|CAFE TURKO|LIL JON|MARTHA|EL RINCONSITO|"
                r"LA COSTA MEXICAN|SAL Y LIMON|STARBUCKS|JOECOFFEE|"
                r"JOHNNY FOLEYS|PANDORA KARAOKE|SQ \*CHUCK|"
                r"WAFFLE CABIN|GDP\*Waffle|Rudys West Seattle|SFO LITTLE CHIHUAHUA|"
                r"BURGER AND KABOB|BREWTOP SOCIAL|DFW WHATABURGER|DILETTANTE MOCHA", re.I), "Restaurants"),
    (re.compile(r"CTLP\*AIRCO", re.I), "House & Maintenance"),  # laundry
    (re.compile(r"Dining", re.I), "Restaurants"),

    # ── Subscriptions ──
    (re.compile(r"CLAUDE\.AI|ANTHROPIC|OPENAI|CHATGPT|OTTER\.AI|"
                r"BITWARDEN|NUULY|CONSUMERREPORTS|HOTMART|"
                r"X CORP|PLAUD\.AI|PLAUD LLC|LOVABLE", re.I), "Subscriptions"),
    (re.compile(r"Netflix|YouTubePremium|YouTube Premiu|Disney|GOOGLE \*Google One|Google One|"
                r"APPLE\.COM/BILL|WAPO\.COM|TWP\*SUB", re.I), "Subscriptions"),
    (re.compile(r"PAYPAL DES:INST XFER ID:DISNEY", re.I), "Subscriptions"),
    (re.compile(r"DROPBOX|BEAUTIFUL\.AI|COPILOT MONEY|CURSOR.*IDE|"
                r"LinkedInPreB|CANVA|PADDLE\.NET|ST SUBSCRIPTIONS|"
                r"SP -ORGANIC LIFE|"
                r"THE ECONOMIST|WAVE.*KATEAH|Kindle Svcs|BLOOMBERG|"
                r"Stamps\.com|Stamps Add Funds|D J\*WSJ|Spotify", re.I), "Subscriptions"),

    # ── Shopping ──
    (re.compile(r"AMAZON|Amazon\.com|Amazon Pharmacy", re.I), "Shopping"),
    (re.compile(r"TARGET|REI\s|REI\.COM|SKECHERS|SEAHAWKS.*RETAIL|"
                r"GREGG.S GREENLAKE|SP RYZESUPERFOODS|"
                r"HOME DEPOT|B&N-BOOKS|BARNES.*NOBLE|FIREWORKS SEATAC|"
                r"SP BASECAMP", re.I), "Shopping"),
    (re.compile(r"IKEA|H&M|GAP US|ARITZIA|ROSS STORE|GOODWILL|"
                r"UNIQLO|BIBA FASHION|SHOPPERS STOP|SPEEDO|"
                r"SP ALLBIRDS|SP KUT FROM|JOANN STORES|SP NORTHWEST YARNS|"
                r"ETSY|WALMART|MINISO|SP RUGGABLE|SP HAPPY HYGGE|"
                r"MEENA BAZAAR|RAJASTHALI|FALABELLA|"
                r"BOLD Laska|BOLD Leila|BOLD BELLO|LASKA|"
                r"BANANA TITAN|INDIGO NATURALLY|BO SIDHPUR|"
                r"ACCESSORIZE|M S JAYPORE|Eliza Handicraft|"
                r"LUCERO HOFMANN|REGALOS RENATA|PALACE SHOP|"
                r"LA TIENDA DE GUADALUPE|SMOKERS PARADIZE|KTC .INDIA|"
                r"KALAGRAM|D&D\b|AMZ\*|SWEETWATER", re.I), "Shopping"),

    # ── Fun & Entertainment ──
    (re.compile(r"SUMMIT RTP|SOUTHGATE ROLLER|XCARET|Entertainment|"
                r"TM \*|TICKETMASTER|JAZZALLEY|ALBUM COVER GROUP", re.I), "Fun & Entertainment"),
    (re.compile(r"WA PARKSRESERVATIONS|SEATTLEAQUARIUM|GEORGIA AQUAR|"
                r"MT ST HELENS|HIGHLINE HERITAGE|BIKEINDEX", re.I), "Fun & Entertainment"),

    # ── Donations ──
    (re.compile(r"CENTREFOREFFECTIVEALTR", re.I), "Donations"),

    # ── Pets ──
    (re.compile(r"doggie|daycare.*pet|pet.*daycare|Chilita|"
                r"LAZY DOG CRAZY DOG|METLIFE PET|ROVER\.COM|PETCO|"
                r"SALTWATERANIMALHOSP", re.I), "Pets"),

    # ── Taxes & Tax Fees ──
    (re.compile(r"IRS|tax payment|Pablo|estate planning|"
                r"M Squared Tax|INTUIT \*TURBOTAX|SEATTLE MUNI INT|Wire Transfer(?! Fee)|"
                r"Zelle.*Lana.*Kurilova", re.I), "Taxes & Tax Fees"),

    # ── Donations ──
    (re.compile(r"CENTREFOREFFECTIVEALTR|GOFNDME|GOFUNDME|"
                r"PAYPAL \*SHOREWOODEL|PP\*SHOREWOOD PTA|BLUEDOT", re.I), "Donations"),

    # ── Catch-alls ──
    (re.compile(r"Monthly Maintenance Fee|MEMBER FEE|Fee/Interest|"
                r"ANNUAL FEE|CASH EQUIVALENT.*FEE|Wire Transfer Fee|Miscellaneous Debit", re.I), "Fees & Bank Charges"),
    (re.compile(r"CITY OF FEDERAL WAY", re.I), "Fun & Entertainment"),
    (re.compile(r"VENMO|PAYPAL|Zelle.*Minh|BKOFAMERICA ATM|"
                r"Zelle.*Esteban|Zelle.*Patricia|Zelle.*Paty|"
                r"Zelle.*Walter|Seattle Network|"
                r"GUSTO|Returned Check|"
                r"\+BOB\b|RAZ\*SMART|EVALO|EVACOL|EXITO WOW|"
                r"WWW\.CLASSACTPORTRAITS|CLAUDIA PRIETO|ASTRA FESTUM", re.I), "Unclassified"),
]


# ── Subcategory rules ─────────────────────────────────────────────────────
# Each entry is (pattern, subcategory). Applied after category is assigned.

SUBCATEGORY_RULES: dict[str, list[tuple[re.Pattern, str]]] = {
    "Utilities": [
        (re.compile(r"T-MOBILE|TMOBILE", re.I), "Cell Phone"),
        (re.compile(r"SEATTLEUTILTIES", re.I), "Electric/Water (Seattle Utilities)"),
        (re.compile(r"SOUTHWEST SUBURBAN", re.I), "Sewer"),
        (re.compile(r"RECOLOGY", re.I), "Trash & Recycling"),
        (re.compile(r"PEMCO", re.I), "Insurance (PEMCO)"),
    ],
    "Childcare": [
        (re.compile(r"WORLDKIDS", re.I), "Zoe Daycare (WorldKids)"),
        (re.compile(r"LINELEADER|RightAtSchool", re.I), "Victoria After School (LineLeader)"),
        (re.compile(r"Zelle.*Danna", re.I), "Spanish Tutor (Danna)"),
        (re.compile(r"YMCA", re.I), "YMCA Kids Programs"),
        (re.compile(r"MY SPANISH NANNY", re.I), "Nanny"),
        (re.compile(r"LITTLE SPOON", re.I), "Baby Food (Little Spoon)"),
        (re.compile(r"SCHOOL OF ROCK", re.I), "Music Lessons (School of Rock)"),
        (re.compile(r"SP WOOM BIKES", re.I), "Kids Bikes"),
    ],
    "House & Maintenance": [
        (re.compile(r"Zelle.*Graciela", re.I), "Cleaning (Graciela)"),
        (re.compile(r"Zelle.*Iris", re.I), "House Helper (Iris)"),
        (re.compile(r"Zelle.*Silvia.*Diaz|Zelle.*Silvia Adriana", re.I), "House Helper (Silvia)"),
        (re.compile(r"Zelle.*Israel", re.I), "Yard (Israel)"),
        (re.compile(r"Zelle.*Francisco", re.I), "Contractor (Francisco)"),
        (re.compile(r"CTLP\*AIRCO", re.I), "Laundry"),
        (re.compile(r"ECOSHIELD", re.I), "Pest Control"),
        (re.compile(r"NUTONE", re.I), "Dry Cleaning"),
    ],
    "Car": [
        (re.compile(r"JPMORGAN CHASE|JPMorgan Chase", re.I), "Subaru Lease"),
        (re.compile(r"SAFEWAY FUEL|76 -|TESLA SUPERCHARGER|CHARGEPOINT|"
                    r"CHEVRON|ARCO|SHELL OIL|COSTCO GAS|E\.S AEROPUERTO|"
                    r"7-ELEVEN|WEST COAST PETROLEUM|AUTOPISTA DEL SOL", re.I), "Gas"),
        (re.compile(r"WSDOT-GOODTOGO", re.I), "Tolls"),
        (re.compile(r"SDOT PAYBYPHONE|PIKE PLACE MARKET PDA|SPOTHERO|DIAMOND PARKING|HONK PARKING", re.I), "Parking"),
        (re.compile(r"PayMyNotice", re.I), "Tickets/Fines"),
        (re.compile(r"CTLP\*CSC SERVICEWORKS", re.I), "Car Wash"),
        (re.compile(r"WA STATE DOL|WA DOL LIC", re.I), "Registration/Licensing"),
    ],
    "Mortgage & Student Loans": [
        (re.compile(r"JPMORGAN CHASE|JPMorgan Chase", re.I), "Shorewood Mortgage"),
        (re.compile(r"Firstmark|Common Bond", re.I), "Student Loan (Firstmark)"),
        (re.compile(r"MOHELA", re.I), "Student Loan (MOHELA)"),
    ],
    "Travel": [
        (re.compile(r"ALASKA AIR|UNITED\s|DELTA AIR|FRONTIER AI|COT\*FLT|Airfare|AIR CAN\*|BRITISH A|VUELING|AMERICAN AI|SOUTHWES|TACA AIR", re.I), "Flights"),
        (re.compile(r"AIRBNB|GUESTRS|VIDANTA|ROYAL SOLARIS|EXPERIENCIAS XCARET|Lodging|NEXION", re.I), "Lodging"),
        (re.compile(r"UBER\s+\*TRIP|LYFT\s+\*RIDE|CLIPPER TRANSIT|ORCA\b|MERPAGO\*TRANSPORTE|MERPAGO\*UBALDO|MERPAGO\*TOURSELSI", re.I), "Rideshare & Transit"),
        (re.compile(r"Stamps\.com|Stamps Add Funds", re.I), "Shipping"),
        (re.compile(r"WIFIONBOARD", re.I), "In-flight WiFi"),
        (re.compile(r"Chairs/Carts|SmarteCarte|Nyx\*SmarteCarte", re.I), "Airport Services"),
        (re.compile(r"CANCUN|OXXO|ASUR|LOS CINCO|SUNSET NEWS|HUDSONNEWS", re.I), "Travel Shopping"),
        (re.compile(r"EXPEDIA", re.I), "Booking Fees"),
    ],
    "Subscriptions": [
        (re.compile(r"CLAUDE\.AI|ANTHROPIC", re.I), "AI Subscriptions"),
        (re.compile(r"OPENAI|CHATGPT", re.I), "AI Subscriptions"),
        (re.compile(r"CURSOR.*IDE", re.I), "AI Subscriptions"),
        (re.compile(r"PADDLE\.NET.*APPCHATBOT", re.I), "AI Subscriptions"),
        (re.compile(r"CANVA", re.I), "AI Subscriptions"),
    ],
    "Fitness & Healthcare": [
        (re.compile(r"PUGET SOUND BASKETBALL", re.I), "Victoria Basketball"),
        (re.compile(r"DENTIST", re.I), "Dental"),
        (re.compile(r"Amazon Pharmacy", re.I), "Pharmacy"),
    ],
    "Therapy & Coaching": [
        (re.compile(r"MARGARITA QUIJANO", re.I), "Therapist (Margarita)"),
        # PAYPAL coaching is handled in classify_subcategory
    ],
    "Restaurants": [
        (re.compile(r"UBER\s+\*EATS|GRUBHUB|DD \*|DLO\*RAPPI|Rappi", re.I), "Delivery"),
    ],
    "Pets": [
        (re.compile(r"LAZY DOG CRAZY DOG", re.I), "Doggie Daycare (Chilita)"),
        (re.compile(r"METLIFE PET", re.I), "Pet Insurance"),
        (re.compile(r"ROVER\.COM", re.I), "Pet Sitting"),
        (re.compile(r"SALTWATERANIMALHOSP|PETCO", re.I), "Vet/Supplies"),
    ],
    "Taxes & Tax Fees": [
        (re.compile(r"IRS", re.I), "Federal Tax"),
        (re.compile(r"SEATTLE MUNI INT", re.I), "City Tax"),
        (re.compile(r"M Squared Tax|INTUIT \*TURBOTAX", re.I), "Tax Preparation"),
        (re.compile(r"Zelle.*Lana.*Kurilova", re.I), "Professional Services"),
        (re.compile(r"Wire Transfer(?! Fee)", re.I), "Estate Planning"),
    ],
    "Investments": [
        (re.compile(r"SOFI SECURITIES", re.I), "SoFi Brokerage"),
        (re.compile(r"VANGUARD", re.I), "Vanguard IRA"),
        (re.compile(r"Manual DB-Bkrg", re.I), "Chase Brokerage"),
        (re.compile(r"CHARLES SCHWAB", re.I), "Schwab Brokerage"),
    ],
    "Income": [
        (re.compile(r"CARBON DIRECT", re.I), "Maria Job Income"),
        (re.compile(r"WA ST EMPLOY SEC", re.I), "Scott's Unemployment"),
        (re.compile(r"VENMO|PAYPAL|Zelle.*from", re.I), "Friends & Family Payments"),
        (re.compile(r"Epoch Artificial", re.I), "Scott's Salary"),
        (re.compile(r"CREDIT-TRAVEL REWARD", re.I), "Credit Card Rewards"),
        (re.compile(r"Manual CR-Bkrg|SOFI SECURITIES", re.I), "Investment Liquidations"),
        # Demo income sources (no-op on real data)
        (re.compile(r"GREENTECH SOLUTIONS", re.I), "Michael Salary"),
        (re.compile(r"PACIFIC NORTHWEST CONSULTING", re.I), "Viviana Salary"),
    ],
}


def classify_subcategory(row: pd.Series) -> str:
    """Assign a subcategory based on category and description."""
    category = row.get("category", "")
    desc = str(row["description"])
    orig_cat = str(row.get("original_category", ""))
    combined = f"{desc} {orig_cat}"

    # Special case for standalone PAYPAL
    if re.match(r"^PAYPAL$", desc, re.I):
        return "Coaching"

    # JPMorgan Chase: $519.50 = car loan, $563.99 = Subaru lease
    amount = row.get("amount", 0)
    if category == "Car" and re.search(r"JPMORGAN CHASE|JPMorgan Chase", desc, re.I):
        return "Car Loan" if abs(abs(amount) - 519.50) < 1 else "Subaru Lease"

    # Shopping: single transactions > $200 → "Large Purchases"
    if category == "Shopping" and abs(amount) > 200:
        return "Large Purchases"

    rules = SUBCATEGORY_RULES.get(category, [])
    for pattern, subcat in rules:
        if pattern.search(combined):
            return subcat

    if category == "Income":
        return "Other Income"

    return ""


def classify_category(row: pd.Series) -> str:
    """Assign a spending category based on description and original_category."""
    flow = row.get("flow_type", "")
    if flow in ("cc_payment", "internal_transfer"):
        return flow  # not a spending category
    if flow == "income":
        return "Income"

    desc = str(row["description"])
    orig_cat = str(row.get("original_category", ""))
    combined = f"{desc} {orig_cat}"
    card_last4 = str(row.get("card_last4", ""))

    # Luthien Expenses: AI tools charged on card 9430 (Maria's Luthien business card)
    if card_last4 == "9430" and re.search(
        r"CLAUDE|ANTHROPIC|OPENAI|CHATGPT|OTTER|CURSOR|COPILOT|PLAUD|BEAUTIFUL\.AI",
        desc, re.I
    ):
        return "Luthien Expenses"

    # Special case: standalone PAYPAL (not Disney/subscriptions) = Maria's coaching
    if re.match(r"^PAYPAL$", desc, re.I):
        return "Therapy & Coaching"

    # JPMorgan Chase: ~$7,246 = mortgage, ~$564 = Subaru auto lease
    if re.search(r"JPMORGAN CHASE|JPMorgan Chase", desc, re.I):
        if abs(row["amount"]) > 1000:
            return "Mortgage & Student Loans"
        else:
            return "Car"

    # Costco always goes to Groceries (overrides Capital One's Gas/Automotive tag)
    if re.search(r"COSTCO|IC\* COSTCO", desc, re.I):
        return "Groceries"

    for pattern, category in CATEGORY_RULES:
        if pattern.search(combined):
            return category

    return "Unclassified"


# ── Main pipeline ─────────────────────────────────────────────────────────

def load_all_transactions() -> pd.DataFrame:
    """Walk the data directory, parse every CSV, and return unified DataFrame."""
    all_frames = []

    all_csvs = list(DATA_ROOT.rglob("*.csv")) + list(DATA_ROOT.rglob("*.CSV"))
    for csv_file in sorted(set(all_csvs)):
        # Skip output files
        if "Monthly" in csv_file.relative_to(DATA_ROOT).parts:
            continue
        if csv_file.name == "all_transactions.csv":
            continue
        parser, account_name = detect_parser(csv_file)
        if parser is None:
            print(f"  ⚠ Skipping unknown file: {csv_file}")
            continue

        print(f"  Reading {csv_file.relative_to(DATA_ROOT)} → {account_name}")
        try:
            df = parser(csv_file, account_name)
            if df is not None and not df.empty:
                # Tag which month folder it came from
                month_folder = csv_file.relative_to(DATA_ROOT).parts[0]
                df["month_folder"] = month_folder
                all_frames.append(df)
        except Exception as e:
            print(f"  ✗ Error parsing {csv_file.name}: {e}")

    if not all_frames:
        print("No transactions found.")
        return pd.DataFrame()

    combined = pd.concat(all_frames, ignore_index=True)

    # Filter out Jan/Feb 2025 (use post_date for filtering)
    combined["post_date"] = pd.to_datetime(combined["post_date"])
    combined = combined[~(
        (combined["post_date"].dt.year == 2025) &
        (combined["post_date"].dt.month.isin([1, 2]))
    )].copy()

    # Exclude spillover transactions: for monthly upload folders (e.g., "Feb26"),
    # exclude transactions whose post_date falls in a later month than the folder's
    # primary month. Annual folders (e.g., "2025") are exempt from this check.
    folder_primary = {}
    for folder, grp in combined.groupby("month_folder"):
        # Skip annual folders (4-digit year names like "2025")
        if re.match(r"^\d{4}$", folder):
            continue
        # Skip folders with data spanning more than 2 months (backfill folders)
        distinct_months = grp["post_date"].dt.to_period("M").nunique()
        if distinct_months > 2:
            continue
        mode = grp["post_date"].dt.to_period("M").mode()
        if not mode.empty:
            folder_primary[folder] = mode.iloc[0]
    spillover = combined["month_folder"].map(folder_primary).notna() & (
        combined["post_date"].dt.to_period("M") > combined["month_folder"].map(folder_primary)
    )
    if spillover.any():
        print(f"  Excluding {spillover.sum()} spillover transaction(s) from incomplete month(s)")
    combined = combined[~spillover].copy()

    # Classify flow types
    combined["flow_type"] = combined.apply(classify_flow_type, axis=1)

    # Classify spending categories and subcategories
    combined["category"] = combined.apply(classify_category, axis=1)
    combined["subcategory"] = combined.apply(classify_subcategory, axis=1)

    # Use post_date as the primary date for reporting
    combined["transaction_date"] = combined["date"]
    combined["date"] = combined["post_date"]

    # Sort by date
    combined = combined.sort_values("date").reset_index(drop=True)

    # Merge transaction notes
    notes_file = Path(__file__).parent / "transaction_notes.json"
    if notes_file.exists():
        import json
        notes = json.loads(notes_file.read_text())
        if notes:
            combined["_tx_key"] = (
                combined["date"].dt.strftime("%Y-%m-%d") + "|" +
                combined["description"] + "|" +
                combined["amount"].round(2).astype(str) + "|" +
                combined["account"]
            )
            combined["notes"] = combined["_tx_key"].map(notes).fillna("")
            combined.drop(columns=["_tx_key"], inplace=True)
            # Reclassify by note content
            scott_ba = combined["notes"].str.contains("Scott Bay Area|Luthien reimbursable", case=False, na=False, regex=True)
            combined.loc[scott_ba, "category"] = "Luthien Expenses"
            combined.loc[scott_ba, "subcategory"] = "Bay Area Trips"
            # Maria's work trips → Work Travel category
            is_travel = combined["category"] == "Travel"
            maria_work = combined["notes"].str.contains(
                "San Jose conference|Maria work trip|Virginia work",
                case=False, na=False, regex=True
            )
            combined.loc[is_travel & maria_work, "category"] = "Work Travel"
            # Crystal Mountain → Fun & Entertainment
            crystal = combined["notes"].str.contains("Crystal Mountain", case=False, na=False)
            crystal_desc = combined["description"].str.contains("CRYSTAL MTN|CRYSTAL MOUNTAIN", case=False, na=False, regex=True)
            combined.loc[crystal | crystal_desc, "category"] = "Fun & Entertainment"
            combined.loc[crystal | crystal_desc, "subcategory"] = "Crystal Mountain"
        else:
            combined["notes"] = ""
    else:
        combined["notes"] = ""

    return combined


def print_summary(df: pd.DataFrame):
    """Print a quick summary of the compiled data."""
    print(f"\n{'='*60}")
    print(f"Total transactions: {len(df)}")
    print(f"Date range: {df['date'].min().date()} → {df['date'].max().date()}")
    print(f"\nTransactions by account:")
    print(df.groupby("account")["amount"].agg(["count", "sum"]).to_string())
    print(f"\nTransactions by flow_type:")
    ft = df.groupby("flow_type")["amount"].agg(["count", "sum"])
    print(ft.to_string())

    # The cash flow view: only spending + income
    cashflow = df[df["flow_type"].isin(["spending", "income"])]
    total_income = cashflow.loc[cashflow["flow_type"] == "income", "amount"].sum()
    total_spending = cashflow.loc[cashflow["flow_type"] == "spending", "amount"].sum()
    print(f"\n{'─'*60}")
    print(f"CASH FLOW (excluding cc_payment & internal_transfer):")
    print(f"  Total income:   ${total_income:>12,.2f}")
    print(f"  Total spending: ${total_spending:>12,.2f}")
    print(f"  Net cash flow:  ${total_income + total_spending:>12,.2f}")

    # Spending by category with subcategories
    spending = df[df["flow_type"] == "spending"].copy()
    spending["abs_amount"] = spending["amount"].abs()
    cat_summary = spending.groupby("category")["abs_amount"].agg(["count", "sum"])
    cat_summary = cat_summary.sort_values("sum", ascending=False)
    cat_summary.columns = ["txns", "total_spent"]
    print(f"\n{'─'*60}")
    print("SPENDING BY CATEGORY & SUBCATEGORY:")
    for cat, row in cat_summary.iterrows():
        print(f"  {cat:<28s} {row['txns']:>4.0f} txns  ${row['total_spent']:>10,.2f}")
        # Show subcategories
        cat_txns = spending[spending["category"] == cat]
        sub_summary = cat_txns.groupby("subcategory")["abs_amount"].agg(["count", "sum"])
        sub_summary = sub_summary.sort_values("sum", ascending=False)
        for sub, srow in sub_summary.iterrows():
            label = sub if sub else "(untagged)"
            print(f"    {label:<26s} {srow['count']:>4.0f} txns  ${srow['sum']:>10,.2f}")
    print(f"  {'TOTAL':<28s} {cat_summary['txns'].sum():>4.0f} txns  ${cat_summary['total_spent'].sum():>10,.2f}")

    # Flag uncategorized
    uncat = spending[spending["category"] == "Uncategorized"]
    if not uncat.empty:
        print(f"\n  ⚠ {len(uncat)} uncategorized transactions — review:")
        for _, r in uncat.iterrows():
            print(f"    {str(r['date'])[:10]}  {r['account']:20s} ${abs(r['amount']):>8.2f}  {r['description']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    print("Compiling all cash flow transactions...\n")
    df = load_all_transactions()
    if not df.empty:
        print_summary(df)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"\nSaved to: {OUTPUT_FILE}")

        # Save per-month files organized by year
        monthly_dir = DATA_ROOT / "Monthly"
        df["_year"] = df["date"].dt.year
        df["_month"] = df["date"].dt.month
        for (year, month), month_df in df.groupby(["_year", "_month"]):
            year_dir = monthly_dir / str(int(year))
            year_dir.mkdir(parents=True, exist_ok=True)
            month_name = pd.Timestamp(year=int(year), month=int(month), day=1).strftime("%B")
            filename = f"{month_name}_{int(year)}.csv"
            month_df.drop(columns=["_year", "_month"]).to_csv(year_dir / filename, index=False)
            print(f"  Saved: Monthly/{int(year)}/{filename} ({len(month_df)} txns)")
        df.drop(columns=["_year", "_month"], inplace=True)
