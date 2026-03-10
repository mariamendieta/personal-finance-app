"""
Generate realistic demo data for Woffieta Finances.
Creates fake CSV files matching all parser formats so the full pipeline can run.

Usage:
    python3 generate_demo_data.py                          # creates Demo/ folder here
    python3 generate_demo_data.py --output ~/Demo-Finances # custom location
    python3 generate_demo_data.py --scale 0.5              # 50% of default amounts

All amounts are 60% of a typical household by default (--scale 0.6).
"""

import argparse
import csv
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

# ── Default scale factor (40% lower than typical) ────────────────────────────
DEFAULT_SCALE = 0.6

# ── Fake merchants & categories ──────────────────────────────────────────────

GROCERY_MERCHANTS = [
    "TRADER JOES #123", "COSTCO WHSE #0045", "SAFEWAY STORE 1234",
    "WHOLEFDS MKT #10567", "QFC #5678", "ALDI STORE 09876",
    "IC* INSTACART GROCERIES",
]
RESTAURANT_MERCHANTS = [
    "CHIPOTLE 2345", "STARBUCKS #12345", "MCDONALDS F12345",
    "PANERA BREAD #4567", "DOMINOS PIZZA 6789", "PHO BAC SUP SHOP",
    "THAI BAMBOO REST", "MOD PIZZA SEATTLE",
]
SHOPPING_MERCHANTS = [
    "AMAZON.COM*1A2B3C", "TARGET 00001234", "REI #45 SEATTLE",
    "IKEA SEATTLE", "ROSS STORES #567", "GOODWILL RETAIL #89",
    "H&M US ONLINE", "SKECHERS USA 456",
]
SUBSCRIPTION_MERCHANTS = [
    "NETFLIX.COM", "SPOTIFY USA", "APPLE.COM/BILL", "DISNEY PLUS",
    "HULU *LIVE TV", "DROPBOX*PLAN", "LINKEDIN PREMIUM",
    "CLAUDE.AI SUBSCRIPTION", "OPENAI *CHATGPT PLUS",
]
ENTERTAINMENT_MERCHANTS = [
    "AMC THEATRES #1234", "SEATTLE AQUARIUM", "WA PARKS RESERVATIONS",
    "MUSEUM OF POP CULTURE", "WOODLAND PARK ZOO",
]
FITNESS_MERCHANTS = [
    "YMCA OF GREATER SEATTLE", "PELOTON MEMBERSHIP",
]
UTILITY_MERCHANTS = [
    "SEATTLEUTILTIES", "PUGET SOUND ENERGY", "XFINITY COMCAST",
    "T-MOBILE PAYMENT",
]
TRAVEL_MERCHANTS = [
    "UNITED AIRLINES 0161234", "AIRBNB * HM1ABC2DE",
    "MARRIOTT HOTEL SEA", "HERTZ RENT-A-CAR", "UBER *TRIP",
]
CHILDCARE_MERCHANTS = [
    "BRIGHT HORIZONS #567", "LITTLE STARS DAYCARE",
]
PET_MERCHANTS = [
    "PETCO #1234", "BANFIELD PET HOSPITAL",
]
DONATION_MERCHANTS = [
    "PLANNED PARENTHOOD", "NPR DONATION",
]
THERAPY_MERCHANTS = [
    "BETTER HELP INC", "HEADSPACE COACHING",
]
HOUSE_MERCHANTS = [
    "HOME DEPOT #4567", "LOWES #12345", "ACE HARDWARE SEA",
]

# Income merchants by source
INCOME_MERCHANTS = {
    "salary": ("GREENTECH SOLUTIONS DIRECT_DEPOSIT", "DIRECT_DEPOSIT"),
    "partner_salary": ("PACIFIC NORTHWEST CONSULTING DIRECT_DEPOSIT", "DIRECT_DEPOSIT"),
    "other": [
        ("INTEREST PAYMENT", "INTEREST_EARNED"),
        ("IRS TREAS 310 TAX REF", "OTHER"),
    ],
}

INTERNAL_TRANSFER_MERCHANTS = [
    "Online Transfer to Checking",
    "Online Transfer from SAV",
    "JPMORGAN CHASE BANK, NA",
    "From Savings - 4557",
]

# ── Amount ranges per category (before scale) ───────────────────────────────

AMOUNT_RANGES = {
    "groceries": (25, 250),
    "restaurants": (10, 80),
    "shopping": (15, 200),
    "subscriptions": (8, 25),
    "entertainment": (15, 80),
    "fitness": (30, 80),
    "utilities": (50, 300),
    "travel": (100, 800),
    "childcare": (800, 1500),
    "pets": (20, 150),
    "donations": (25, 100),
    "therapy": (80, 200),
    "house": (30, 300),
}

# ── Portfolio tickers ────────────────────────────────────────────────────────

# 1. Joint Brokerage (Chase 82-col format) — taxable
DEMO_JOINT_BROKERAGE = [
    ("VOO", "Vanguard S&P 500 ETF", "US Equity", "Large Cap", 520.45, 85),
    ("VTI", "Vanguard Total Stock Market ETF", "US Equity", "Broad Market", 280.30, 60),
    ("VXUS", "Vanguard Total Intl Stock ETF", "International Equity", "Broad Market", 62.15, 200),
    ("BND", "Vanguard Total Bond Market ETF", "Fixed Income", "Broad Market", 74.50, 150),
    ("VNQ", "Vanguard Real Estate ETF", "Real Estate", "Broad Market", 88.20, 40),
    ("AAPL", "Apple Inc", "US Equity", "Large Cap", 225.50, 30),
    ("MSFT", "Microsoft Corp", "US Equity", "Large Cap", 420.80, 20),
    ("GOOGL", "Alphabet Inc", "US Equity", "Large Cap", 175.60, 25),
    ("AMZN", "Amazon.com Inc", "US Equity", "Large Cap", 185.40, 15),
    ("NVDA", "NVIDIA Corp", "US Equity", "Large Cap", 135.20, 40),
    ("MJLXX", "JPMorgan Liquid Assets MM", "Cash", "Short Term", 1.00, 5000),
]

# 2. Michael's Roth IRA (Chase 82-col format)
DEMO_MICHAEL_ROTH = [
    ("VOO", "Vanguard S&P 500 ETF", "US Equity", "Large Cap", 520.45, 30),
    ("VXUS", "Vanguard Total Intl Stock ETF", "International Equity", "Broad Market", 62.15, 100),
    ("BND", "Vanguard Total Bond Market ETF", "Fixed Income", "Broad Market", 74.50, 80),
    ("VNQ", "Vanguard Real Estate ETF", "Real Estate", "Broad Market", 88.20, 20),
    ("MJLXX", "JPMorgan Liquid Assets MM", "Cash", "Short Term", 1.00, 8000),
]

# 3. Michael's 401k (Empower/simple format)
DEMO_MICHAEL_401K = [
    ("Fidelity 500 Index", 25000),
    ("Fidelity Total International Index", 18000),
    ("Fidelity Mid Cap Index", 8000),
    ("Fidelity Small Cap Index", 5000),
    ("Fidelity U.S. Bond Index", 10000),
    ("FID GROWTH CO POOL CL 3", 4000),
]

# 4. Viviana's Roth IRA (marias_roth format)
DEMO_VIVIANA_ROTH = [
    ("VBTLX", "Vanguard Total Bond Market Index Fund", 9.81, 800),
    ("VFIAX", "Vanguard 500 Index Fund", 628.68, 15),
    ("VWO", "Vanguard FTSE Emerging Markets ETF", 55.89, 120),
    ("AVDV", "Avantis Intl Small Cap Value ETF", 103.88, 40),
    ("VMFXX", "Vanguard Federal Money Market Fund", 1.00, 4000),
]

# 5. Viviana's 401k (Vanguard format)
DEMO_VIVIANA_401K = [
    ("VOO", "+35.20%", 10.0, 30, 15600),
    ("VXUS", "+12.50%", 8.0, 50, 3100),
    ("BND", "+5.80%", 6.0, 80, 5960),
    ("VTI", "+28.90%", 15.0, 20, 5610),
    ("VTIP", "+8.20%", 5.0, 60, 3780),
    ("VMFXX", "+4.10%", 1.0, 2500, 2500),
]


def rand_amount(low, high, scale):
    """Generate a random amount within range, scaled."""
    return round(random.uniform(low, high) * scale, 2)


def rand_date_in_month(year, month):
    """Random date within a given month."""
    if month == 12:
        last_day = 31
    else:
        last_day = (date(year, month + 1, 1) - timedelta(days=1)).day
    day = random.randint(1, last_day)
    return date(year, month, day)


def generate_chase_card_csv(filepath, year, month, scale, merchants_mix):
    """Generate a Chase credit card CSV (Aeroplan/AmazonPrime/United format)."""
    rows = []
    for category, merchant_list, amt_key, count in merchants_mix:
        for _ in range(count):
            d = rand_date_in_month(year, month)
            post = d + timedelta(days=random.randint(1, 3))
            # Clamp post to same month
            if post.month != month:
                post = d
            merchant = random.choice(merchant_list)
            low, high = AMOUNT_RANGES[amt_key]
            amount = -rand_amount(low, high, scale)
            rows.append({
                "Transaction Date": d.strftime("%m/%d/%Y"),
                "Post Date": post.strftime("%m/%d/%Y"),
                "Description": merchant,
                "Category": category,
                "Type": "Sale",
                "Amount": f"{amount:.2f}",
                "Memo": "",
            })

    rows.sort(key=lambda r: r["Post Date"])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Transaction Date", "Post Date", "Description",
                                          "Category", "Type", "Amount", "Memo"])
        w.writeheader()
        w.writerows(rows)


def generate_capital_one_csv(filepath, year, month, scale, merchants_mix):
    """Generate a Capital One CSV (VentureX/VentureOne format)."""
    rows = []
    for category, merchant_list, amt_key, count in merchants_mix:
        for _ in range(count):
            d = rand_date_in_month(year, month)
            post = d + timedelta(days=random.randint(1, 3))
            if post.month != month:
                post = d
            merchant = random.choice(merchant_list)
            low, high = AMOUNT_RANGES[amt_key]
            amount = rand_amount(low, high, scale)
            rows.append({
                "Transaction Date": d.strftime("%Y-%m-%d"),
                "Posted Date": post.strftime("%Y-%m-%d"),
                "Card No.": "1234",
                "Description": merchant,
                "Category": category,
                "Debit": f"{amount:.2f}",
                "Credit": "",
            })

    rows.sort(key=lambda r: r["Posted Date"])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Transaction Date", "Posted Date", "Card No.",
                                          "Description", "Category", "Debit", "Credit"])
        w.writeheader()
        w.writerows(rows)


def generate_alaska_csv(filepath, year, month, scale, merchants_mix):
    """Generate an Alaska/BoA card CSV."""
    rows = []
    for _category, merchant_list, amt_key, count in merchants_mix:
        for _ in range(count):
            d = rand_date_in_month(year, month)
            merchant = random.choice(merchant_list)
            low, high = AMOUNT_RANGES[amt_key]
            amount = -rand_amount(low, high, scale)
            rows.append({
                "Posted Date": d.strftime("%m/%d/%Y"),
                "Reference Number": str(random.randint(10000000, 99999999)),
                "Payee": merchant,
                "Address": "SEATTLE WA",
                "Amount": f"{amount:.2f}",
            })

    rows.sort(key=lambda r: r["Posted Date"])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Posted Date", "Reference Number", "Payee",
                                          "Address", "Amount"])
        w.writeheader()
        w.writerows(rows)


def generate_sofi_csv(filepath, year, month, scale, is_checking=True):
    """Generate a SoFi checking or savings CSV."""
    rows = []
    d_base = date(year, month, 1)

    if is_checking:
        # Michael's salary (2 per month, higher earner)
        for day_offset in [1, 15]:
            d = date(year, month, min(day_offset, 28))
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": INCOME_MERCHANTS["salary"][0],
                "Type": INCOME_MERCHANTS["salary"][1],
                "Amount": f"{rand_amount(4000, 5500, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        # Viviana's salary (2 per month, lower earner)
        for day_offset in [1, 15]:
            d = date(year, month, min(day_offset, 28))
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": INCOME_MERCHANTS["partner_salary"][0],
                "Type": INCOME_MERCHANTS["partner_salary"][1],
                "Amount": f"{rand_amount(2000, 3000, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        # Other income (occasional — interest, refunds, side gigs)
        if month in [3, 6, 9, 12]:  # quarterly interest
            d = date(year, month, min(20, 28))
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": "INTEREST PAYMENT",
                "Type": "INTEREST_EARNED",
                "Amount": f"{rand_amount(30, 80, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        if month == 4:  # tax refund
            d = date(year, month, min(15, 28))
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": "IRS TREAS 310 TAX REF",
                "Type": "CHECK_DEPOSIT",
                "Amount": f"{rand_amount(1500, 3500, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        if month in [7, 11]:  # occasional side income
            d = rand_date_in_month(year, month)
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": random.choice(["FREELANCE DEPOSIT", "CHECK_DEPOSIT CONSULTING"]),
                "Type": "CHECK_DEPOSIT",
                "Amount": f"{rand_amount(500, 1500, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        # Mortgage
        d = date(year, month, min(5, 28))
        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Description": "JPMORGAN CHASE",
            "Type": "DIRECT_PAY",
            "Amount": f"{-rand_amount(4000, 4500, scale):.2f}",
            "Current balance": "10000.00",
            "Status": "Posted",
        })
        # Car lease
        d = date(year, month, min(10, 28))
        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Description": "JPMORGAN CHASE",
            "Type": "DIRECT_PAY",
            "Amount": f"{-rand_amount(400, 500, scale):.2f}",
            "Current balance": "10000.00",
            "Status": "Posted",
        })
        # CC payments (internal transfers)
        for cc_name in ["CHASE CREDIT CRD AUTOPAY", "CAPITAL ONE MOBILE PMT"]:
            d = rand_date_in_month(year, month)
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": cc_name,
                "Type": "DIRECT_PAY",
                "Amount": f"{-rand_amount(1500, 3000, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
        # Some spending
        for _ in range(5):
            d = rand_date_in_month(year, month)
            merchant = random.choice(["Zelle Payment to Alex", "Zelle Payment to Sam",
                                      "VENMO PAYMENT", "DIRECT_PAY UTILITIES"])
            rows.append({
                "Date": d.strftime("%Y-%m-%d"),
                "Description": merchant,
                "Type": "ZELLE" if "Zelle" in merchant else "DIRECT_PAY",
                "Amount": f"{-rand_amount(50, 500, scale):.2f}",
                "Current balance": "10000.00",
                "Status": "Posted",
            })
    else:
        # Savings — mostly interest and transfers
        d = date(year, month, min(28, 28))
        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Description": "INTEREST PAYMENT",
            "Type": "INTEREST_EARNED",
            "Amount": f"{rand_amount(15, 40, scale):.2f}",
            "Current balance": "15000.00",
            "Status": "Posted",
        })
        # Transfer in
        d = rand_date_in_month(year, month)
        rows.append({
            "Date": d.strftime("%Y-%m-%d"),
            "Description": "From Checking - 1234",
            "Type": "OTHER",
            "Amount": f"{rand_amount(500, 1500, scale):.2f}",
            "Current balance": "15000.00",
            "Status": "Posted",
        })

    rows.sort(key=lambda r: r["Date"])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["Date", "Description", "Type",
                                          "Amount", "Current balance", "Status"])
        w.writeheader()
        w.writerows(rows)


def generate_boa_bank_csv(filepath, year, month, scale, is_checking=True):
    """Generate a BoA checking or savings CSV with summary header."""
    rows_data = []

    if is_checking:
        # A few transactions
        for _ in range(3):
            d = rand_date_in_month(year, month)
            rows_data.append((d.strftime("%m/%d/%Y"),
                              random.choice(["ONLINE TRANSFER", "POS PURCHASE", "ATM WITHDRAWAL"]),
                              f"{-rand_amount(20, 200, scale):.2f}",
                              "5000.00"))
        # Interest
        d = date(year, month, min(28, 28))
        rows_data.append((d.strftime("%m/%d/%Y"), "INTEREST PAYMENT", f"{rand_amount(2, 10, scale):.2f}", "5000.00"))
    else:
        d = date(year, month, min(28, 28))
        rows_data.append((d.strftime("%m/%d/%Y"), "INTEREST PAYMENT", f"{rand_amount(5, 20, scale):.2f}", "8000.00"))

    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        # Summary header section (BoA format)
        f.write(f"Summary for {month}/{year}\n")
        f.write("Beginning balance,5000.00\n")
        f.write("Total credits,100.00\n")
        f.write("Total debits,-200.00\n")
        f.write("Ending balance,4900.00\n")
        f.write("\n")
        # Transaction header
        f.write("Date,Description,Amount,Running Bal.\n")
        for row in rows_data:
            f.write(f"{row[0]},{row[1]},{row[2]},{row[3]}\n")


def generate_chase_checking_csv(filepath, year, month, scale):
    """Generate a Chase checking CSV with trailing commas."""
    rows = []

    # A few transactions
    merchants = [
        ("ZELLE PAYMENT TO ALEX", "DEBIT", -200),
        ("ZELLE PAYMENT FROM PAT", "CREDIT", 150),
        ("CHECK DEPOSIT", "CREDIT", 500),
        ("ATM WITHDRAWAL", "DEBIT", -100),
    ]
    for desc, txn_type, base_amt in merchants:
        d = rand_date_in_month(year, month)
        amt = base_amt * scale * random.uniform(0.8, 1.2)
        rows.append({
            "Details": txn_type,
            "Posting Date": d.strftime("%m/%d/%Y"),
            "Description": desc,
            "Amount": f"{amt:.2f}",
            "Type": txn_type,
            "Balance": "3000.00",
            "Check or Slip #": "",
        })

    rows.sort(key=lambda r: r["Posting Date"])
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        # Write with trailing comma (Chase quirk)
        f.write("Details,Posting Date,Description,Amount,Type,Balance,Check or Slip #,\n")
        for r in rows:
            f.write(f"{r['Details']},{r['Posting Date']},{r['Description']},"
                    f"{r['Amount']},{r['Type']},{r['Balance']},{r['Check or Slip #']},\n")


# ── Portfolio generators ─────────────────────────────────────────────────────

def generate_chase_holdings_csv(filepath, holdings, account_name, scale):
    """Generate Chase 82-column holdings CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # We need many columns to match the 82-col format. Key ones used by parser:
    # Asset Class, Asset Strategy, Description, Ticker, Quantity, Price, Value,
    # Cost, Unrealized Gain/Loss (%), Pricing Date
    cols = [
        "Account Number", "Account Name", "Account Type Desc",
        "Asset Class", "Asset Strategy", "Asset Strategy Detail",
        "Description", "Ticker", "CUSIP", "Quantity", "Price",
        "Value", "Cost", "Unrealized Gain/Loss ($)",
        "Unrealized Gain/Loss (%)", "Pricing Date", "As of",
    ]
    # Pad to ~82 columns
    for i in range(len(cols), 82):
        cols.append(f"Col{i}")

    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for ticker, desc, asset_class, strategy, price, qty in holdings:
            qty_s = qty * scale
            value = round(price * qty_s, 2)
            cost = round(value * random.uniform(0.75, 0.95), 2)
            gl = round(value - cost, 2)
            gl_pct = round((gl / cost) * 100, 2) if cost > 0 else 0
            row = [
                "XXXX1234", account_name, "BROKERAGE",
                asset_class, strategy, strategy,
                desc, ticker, "000000000",
                f"{qty_s:.3f}", f"${price:.2f}",
                f"${value:,.2f}", f"${cost:,.2f}",
                f"${gl:,.2f}", f"{gl_pct:.2f}",
                "03/09/2026", "03/09/2026",
            ]
            # Pad
            row.extend([""] * (82 - len(row)))
            w.writerow(row)
        # FOOTNOTES row
        footnote_row = ["FOOTNOTES"] + [""] * 81
        w.writerow(footnote_row)


def generate_sofi_managed_csv(filepath, holdings, scale):
    """Generate SoFi managed portfolio CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ticker", "Company", "Current Allocation", "Market Price",
                     "Unrealized Gain", "Total Value"])
        for ticker, desc, company, alloc, price, qty in holdings:
            qty_s = qty * scale
            value = round(price * qty_s, 2)
            gain = round(value * random.uniform(-0.05, 0.15), 2)
            t = ticker if ticker else ""
            w.writerow([t, company if not ticker else desc,
                        f"{alloc}%", f"${price:.2f}",
                        f"${gain:,.2f}", f"${value:,.2f}"])


def generate_sofi_brokerage_csv(filepath, holdings, scale):
    """Generate SoFi self-directed brokerage CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ticker", "Shares", "Market Price", "Unrealized Gain", "Total Value"])
        for ticker, qty, price, gain_base in holdings:
            qty_s = qty * scale
            value = round(price * qty_s, 2)
            gain = round(gain_base * scale * random.uniform(0.8, 1.2), 2)
            w.writerow([ticker, f"{qty_s:.4f}", f"${price:.2f}",
                        f"${gain:,.2f}", f"${value:,.2f}"])


def generate_marias_roth_csv(filepath, holdings, scale):
    """Generate Maria's Roth IRA CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    total = 0
    rows = []
    for ticker, name, price, qty in holdings:
        qty_s = qty * scale
        value = round(price * qty_s, 2)
        total += value
        rows.append([ticker, name, f"${price:.2f}", "+$0.50", "+0.25%",
                      f"{qty_s:.3f}", "\u2013", "\u2013", f"${value:,.2f}"])
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Symbol", "Name", "Price", "$ Change", "% Change",
                     "Quantity", "$ Unrealized Gain/Loss",
                     "% Unrealized Gain/Loss", "Current Balance"])
        for r in rows:
            w.writerow(r)
        w.writerow(["Total", "", "", "", "", "", "", "", f"${total:,.2f}"])


def generate_401k_simple_csv(filepath, holdings, scale):
    """Generate Empower 401k CSV (Investment/Balance format)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Investment", "Balance"])
        for fund, balance in holdings:
            bal = round(balance * scale, 2)
            w.writerow([fund, f"${bal:,.2f}"])


def generate_401k_vanguard_csv(filepath, holdings, scale):
    """Generate Vanguard 401k CSV (Fund/Shares/Market Value format)."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Fund", "Last 7 Days", "Your All Time", "Current Weight",
                     "# of Shares", "Market Value"])
        for fund, all_time, weight, shares, value in holdings:
            shares_s = shares * scale
            value_s = round(value * scale, 2)
            w.writerow([fund, "+0.50%", all_time, f"{weight}%",
                        f"{shares_s:.4f}", f"${value_s:,.2f}"])


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="Generate demo data for Woffieta Finances")
    parser.add_argument("--output", type=str, default=None,
                        help="Output directory (default: Demo/ in current folder)")
    parser.add_argument("--scale", type=float, default=DEFAULT_SCALE,
                        help=f"Amount scale factor (default: {DEFAULT_SCALE})")
    args = parser.parse_args()

    output = Path(args.output) if args.output else Path(__file__).resolve().parent / "Demo"
    scale = args.scale

    if output.exists():
        print(f"Removing existing {output}...")
        shutil.rmtree(output)

    print(f"Generating demo data in {output} (scale={scale})...")

    # Copy Python scripts from Production/
    src = Path(__file__).resolve().parent / "Production"
    for script in ["cashflow.py", "generate_report.py", "portfolio.py", "dashboard.py"]:
        script_path = src / script
        if script_path.exists():
            dest = output / script
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(script_path, dest)
            print(f"  Copied {script}")

    # ── Generate 12 months of cash flow data ─────────────────────────────────
    # March 2025 through February 2026
    months = []
    for y in [2025]:
        for m in range(3, 13):
            months.append((y, m))
    for m in range(1, 3):
        months.append((2026, m))

    cf_root = output / "CashFlow"

    # Each month gets its own folder (e.g., Mar25, Apr25, Jan26)
    for year, month in months:
        month_abbr = date(year, month, 1).strftime("%b")
        folder_name = f"{month_abbr}{str(year)[-2:]}"

        cc_dir = cf_root / folder_name / "Credit Cards"
        bank_dir = cf_root / folder_name / "Checking and Savings"

        # -- Aeroplan (Chase card) — main spending card --
        aeroplan_mix = [
            ("Food & Drink", RESTAURANT_MERCHANTS, "restaurants", random.randint(8, 15)),
            ("Groceries", GROCERY_MERCHANTS, "groceries", random.randint(4, 8)),
            ("Shopping", SHOPPING_MERCHANTS, "shopping", random.randint(3, 6)),
            ("Bills & Utilities", SUBSCRIPTION_MERCHANTS, "subscriptions", random.randint(3, 5)),
            ("Entertainment", ENTERTAINMENT_MERCHANTS, "entertainment", random.randint(1, 3)),
            ("Health & Wellness", FITNESS_MERCHANTS, "fitness", random.randint(0, 2)),
            ("Travel", TRAVEL_MERCHANTS, "travel", random.randint(0, 3)),
        ]
        suffix = f"_{folder_name}.CSV" if year == 2025 else f"_{folder_name}.CSV"
        generate_chase_card_csv(cc_dir / f"Aeroplan{suffix}", year, month, scale, aeroplan_mix)

        # -- AmazonPrime (Chase card) --
        amazon_mix = [
            ("Shopping", SHOPPING_MERCHANTS, "shopping", random.randint(2, 5)),
            ("Groceries", GROCERY_MERCHANTS, "groceries", random.randint(1, 3)),
        ]
        generate_chase_card_csv(cc_dir / f"AmazonPrime{suffix}", year, month, scale, amazon_mix)

        # -- VentureX (Capital One) — travel card --
        venturex_mix = [
            ("Dining", RESTAURANT_MERCHANTS, "restaurants", random.randint(3, 8)),
            ("Merchandise", SHOPPING_MERCHANTS, "shopping", random.randint(1, 3)),
            ("Travel", TRAVEL_MERCHANTS, "travel", random.randint(1, 4) if month in [6, 7, 8, 12] else random.randint(0, 1)),
            ("Phone/Cable", SUBSCRIPTION_MERCHANTS[:3], "subscriptions", random.randint(1, 2)),
        ]
        cap1_suffix = f"_{folder_name}.csv"
        generate_capital_one_csv(cc_dir / f"VentureX{cap1_suffix}", year, month, scale, venturex_mix)

        # -- Alaska (BoA card) — occasional use --
        alaska_mix = [
            ("Shopping", SHOPPING_MERCHANTS, "shopping", random.randint(0, 2)),
            ("Dining", RESTAURANT_MERCHANTS, "restaurants", random.randint(0, 2)),
        ]
        generate_alaska_csv(cc_dir / f"Alaska{cap1_suffix}", year, month, scale, alaska_mix)

        # -- SoFi Joint Checking --
        generate_sofi_csv(bank_dir / f"SOFI-JointChecking{cap1_suffix}", year, month, scale, is_checking=True)

        # -- SoFi Joint Savings --
        generate_sofi_csv(bank_dir / f"SOFI-JointSavings{cap1_suffix}", year, month, scale, is_checking=False)

        # -- BoA Checking --
        generate_boa_bank_csv(bank_dir / f"BoA-Checking{cap1_suffix}", year, month, scale, is_checking=True)

        # -- BoA Savings --
        generate_boa_bank_csv(bank_dir / f"BoA-Savings{cap1_suffix}", year, month, scale, is_checking=False)

        # -- Chase Checking --
        generate_chase_checking_csv(bank_dir / f"Chase-Checking{cap1_suffix}", year, month, scale)

        print(f"  Generated {date(year, month, 1).strftime('%B %Y')} cash flow")

    # ── Generate portfolio snapshot ──────────────────────────────────────────
    snapshot_date = "2026-03-09"
    inv_dir = output / "InvestmentPortfolio" / snapshot_date / "Investments&Balances"

    # 1. Joint Brokerage (taxable)
    generate_chase_holdings_csv(
        inv_dir / "JointBrokerage.csv",
        DEMO_JOINT_BROKERAGE, "JOINT BROKERAGE", scale)

    # 2. Michael's Roth IRA
    generate_chase_holdings_csv(
        inv_dir / "MichaelsRothIRA.csv",
        DEMO_MICHAEL_ROTH, "MICHAEL ROTH IRA", scale)

    # 3. Michael's 401k
    generate_401k_simple_csv(inv_dir / "Michaels 401k.csv", DEMO_MICHAEL_401K, scale)

    # 4. Viviana's Roth IRA
    generate_marias_roth_csv(inv_dir / "Vivianas Roth IRA.csv", DEMO_VIVIANA_ROTH, scale)

    # 5. Viviana's 401k
    generate_401k_vanguard_csv(inv_dir / "Vivianas 401k.csv", DEMO_VIVIANA_401K, scale)

    print(f"  Generated portfolio snapshot ({snapshot_date})")

    # ── Summary ──────────────────────────────────────────────────────────────
    print(f"\nDone! Demo data generated in: {output}")
    print(f"\nTo run the demo:")
    print(f"  cd \"{output}\"")
    print(f"  python3 cashflow.py")
    print(f"  python3 generate_report.py")
    print(f"  python3 portfolio.py")
    print(f"  python3 -m streamlit run dashboard.py")


if __name__ == "__main__":
    main()
