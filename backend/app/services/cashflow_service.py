"""Cash flow data service — wraps existing cashflow.py logic."""

import re
import importlib.util
import types
from functools import lru_cache
from pathlib import Path

import pandas as pd

from ..config import DATA_DIR, CASHFLOW_MONTHLY


def _load_cashflow_module():
    """Import the cashflow.py module from the data directory."""
    module_path = DATA_DIR / "cashflow.py"
    spec = importlib.util.spec_from_file_location("cashflow", str(module_path))
    mod = types.ModuleType("cashflow")
    mod.__file__ = str(module_path)
    spec.loader.exec_module(mod)
    return mod


@lru_cache(maxsize=1)
def _load_all_monthly_csvs() -> pd.DataFrame:
    """Load all monthly CSV files into a single DataFrame."""
    frames = []
    for csv_file in sorted(CASHFLOW_MONTHLY.rglob("*.csv")):
        df = pd.read_csv(csv_file, parse_dates=["post_date"])
        frames.append(df)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["month"] = df["post_date"].dt.to_period("M")
    df["month_dt"] = df["post_date"].dt.to_period("M").dt.to_timestamp()
    return df


def invalidate_cache():
    _load_all_monthly_csvs.cache_clear()


def get_cashflow_data(months: int = 12) -> pd.DataFrame:
    """Get cash flow data filtered to last N months."""
    df = _load_all_monthly_csvs()
    if df.empty:
        return df
    latest_month = df["month"].max()
    cutoff = (latest_month - (months - 1)).to_timestamp()
    return df[df["month_dt"] >= cutoff].copy()


# ── Display category mapping (from dashboard.py) ──

KEEP_CATEGORIES = {
    "Childcare", "Subscriptions", "Taxes & Tax Fees", "Travel",
    "House & Maintenance", "Utilities",
}
DEBT_MERGE = {"Mortgage & Student Loans", "Car"}
OTHER_MERGE = {
    "Fitness & Healthcare", "Unclassified", "Groceries", "Pets",
    "Restaurants", "Shopping", "Donations", "Fees & Bank Charges",
    "Fun & Entertainment", "Therapy & Coaching", "Investments",
}


def map_display_category(cat: str) -> str:
    if cat in KEEP_CATEGORIES:
        return cat
    if cat in DEBT_MERGE:
        return "Mortgage, Loans & Car"
    return "Other Expenses"


CATEGORY_COLORS = {
    "Mortgage, Loans & Car": "#1B4965",
    "Childcare": "#2D6A4F",
    "Taxes & Tax Fees": "#E07A5F",
    "Travel": "#E07A5F",
    "Other Expenses": "#6B5E52",
    "Utilities": "#E9A820",
    "House & Maintenance": "#52B788",
    "Subscriptions": "#9A9A9A",
}

DISPLAY_CATEGORY_ORDER = [
    "Mortgage, Loans & Car", "Childcare", "Taxes & Tax Fees", "Travel",
    "Other Expenses", "Utilities", "House & Maintenance", "Subscriptions",
]

# ── Vendor normalization ──

VENDOR_RULES = [
    (re.compile(r"JPMORGAN CHASE|JPMorgan Chase", re.I), "JPMorgan Chase"),
    (re.compile(r"WORLDKIDS", re.I), "Worldkids School"),
    (re.compile(r"IC\*.*COSTCO|IC\*.*INSTACAR|IC\* INSTACART|INSTACART", re.I), "Instacart"),
    (re.compile(r"COSTCO WHSE|COSTCO GAS", re.I), "Costco"),
    (re.compile(r"UBER\s+\*EATS", re.I), "Uber Eats"),
    (re.compile(r"UBER\s+\*TRIP", re.I), "Uber Rides"),
    (re.compile(r"^VENMO", re.I), "Venmo"),
    (re.compile(r"^Zelle", re.I), "Zelle Payments"),
    (re.compile(r"^PAYPAL", re.I), "PayPal"),
    (re.compile(r"TACA AIR", re.I), "TACA Air"),
    (re.compile(r"^IRS", re.I), "IRS"),
    (re.compile(r"T-MOBILE|TMOBILE", re.I), "T-Mobile"),
    (re.compile(r"PEMCO", re.I), "Pemco Insurance"),
    (re.compile(r"SEATTLEUTILTIES|SEATTLE UTIL", re.I), "Seattle Utilities"),
    (re.compile(r"MOHELA", re.I), "Mohela"),
    (re.compile(r"TARGET\s", re.I), "Target"),
    (re.compile(r"AMAZON|Amazon\.com|AMZN", re.I), "Amazon"),
    (re.compile(r"A ?B HOTELS", re.I), "AB Hotels"),
    (re.compile(r"NORBU THE MONTANNA", re.I), "Norbu The Montanna"),
    (re.compile(r"AIRBNB", re.I), "Airbnb"),
    (re.compile(r"VIDANTA", re.I), "Vidanta"),
    (re.compile(r"LINELEADER", re.I), "LineLeader"),
    (re.compile(r"YMCA", re.I), "YMCA"),
    (re.compile(r"SAFEWAY", re.I), "Safeway"),
    (re.compile(r"QFC", re.I), "QFC"),
    (re.compile(r"TRADER JOE", re.I), "Trader Joe's"),
    (re.compile(r"ORGANIC LIFE START", re.I), "Organic Life Start"),
    (re.compile(r"BANK OF AMERICA", re.I), "Bank of America"),
    (re.compile(r"COT\*FLT", re.I), "COT*FLT (Flights)"),
    (re.compile(r"VANGUARD BUY", re.I), "Vanguard Buy"),
]


def normalize_vendor(desc: str) -> str:
    for pattern, name in VENDOR_RULES:
        if pattern.search(desc):
            return name
    return desc


# ── API data builders ──

def get_summary(months: int = 12) -> dict:
    df = get_cashflow_data(months)
    if df.empty:
        return {"total_income": 0, "total_spending": 0, "net_income": 0,
                "months_available": []}
    spending = df[df["flow_type"] == "spending"]
    income = df[df["flow_type"] == "income"]
    total_income = float(income["amount"].sum())
    total_spending = float(spending["amount"].abs().sum())
    months_available = sorted(df["month_dt"].unique().astype(str).tolist())
    return {
        "total_income": total_income,
        "total_spending": total_spending,
        "net_income": total_income - total_spending,
        "months_available": months_available,
    }


def get_monthly_expenses(months: int = 12) -> list[dict]:
    df = get_cashflow_data(months)
    if df.empty:
        return []
    spending = df[df["flow_type"] == "spending"].copy()
    spending["display_category"] = spending["category"].apply(map_display_category)

    # Detail level (for hover breakdowns)
    detail = (
        spending.groupby(["month_dt", "display_category", "category"])["amount"]
        .sum().abs().reset_index()
    )
    # Aggregate to display category
    agg = (
        detail.groupby(["month_dt", "display_category"])["amount"]
        .sum().reset_index()
    )
    # Build breakdown per display_category per month
    breakdowns = (
        detail.groupby(["month_dt", "display_category"], group_keys=False)
        .apply(lambda g: [
            {"category": row["category"], "amount": float(row["amount"])}
            for _, row in g.sort_values("amount", ascending=False).iterrows()
        ], include_groups=False)
        .reset_index(name="breakdown")
    )
    merged = agg.merge(breakdowns, on=["month_dt", "display_category"])

    result = []
    for _, row in merged.iterrows():
        result.append({
            "month": row["month_dt"].strftime("%Y-%m-%d"),
            "display_category": row["display_category"],
            "amount": float(row["amount"]),
            "color": CATEGORY_COLORS.get(row["display_category"], "#999"),
            "breakdown": row["breakdown"],
        })
    return result


def get_monthly_income(months: int = 12) -> list[dict]:
    df = get_cashflow_data(months)
    if df.empty:
        return []
    income = df[df["flow_type"] == "income"].copy()
    income["subcategory"] = income["subcategory"].fillna("Other Income")
    inc_by_src = (
        income.groupby(["month_dt", "subcategory"])["amount"]
        .sum().reset_index()
    )
    return [
        {
            "month": row["month_dt"].strftime("%Y-%m-%d"),
            "subcategory": row["subcategory"],
            "amount": float(row["amount"]),
        }
        for _, row in inc_by_src.iterrows()
    ]


def get_net_income(months: int = 12) -> list[dict]:
    df = get_cashflow_data(months)
    if df.empty:
        return []
    spending = df[df["flow_type"] == "spending"]
    income = df[df["flow_type"] == "income"]
    all_months = sorted(df["month_dt"].unique())
    all_idx = pd.DatetimeIndex(all_months)

    monthly_income = income.groupby("month_dt")["amount"].sum().reindex(all_idx, fill_value=0)
    monthly_spending = spending.groupby("month_dt")["amount"].sum().abs().reindex(all_idx, fill_value=0)
    monthly_net = monthly_income - monthly_spending
    cumulative = monthly_net.cumsum()

    return [
        {
            "month": m.strftime("%Y-%m-%d"),
            "income": float(monthly_income[m]),
            "spending": float(monthly_spending[m]),
            "net": float(monthly_net[m]),
            "cumulative": float(cumulative[m]),
        }
        for m in all_idx
    ]


def get_spending_by_category(months: int = 12) -> list[dict]:
    df = get_cashflow_data(months)
    if df.empty:
        return []
    spending = df[df["flow_type"] == "spending"]
    cat_totals = (
        spending.groupby("category")["amount"].sum().abs()
        .sort_values(ascending=False).reset_index()
    )
    total = cat_totals["amount"].sum()
    return [
        {
            "category": row["category"],
            "total": float(row["amount"]),
            "percent": round(float(row["amount"]) / total * 100, 1) if total else 0,
        }
        for _, row in cat_totals.iterrows()
    ]


def get_top_vendors(months: int = 12, limit: int = 10) -> list[dict]:
    df = get_cashflow_data(months)
    if df.empty:
        return []
    spending = df[df["flow_type"] == "spending"].copy()
    spending["vendor"] = spending["description"].apply(normalize_vendor)
    total = spending["amount"].abs().sum()
    vendor_totals = (
        spending.groupby("vendor")["amount"].sum().abs()
        .sort_values(ascending=False).head(limit).reset_index()
    )
    return [
        {
            "vendor": row["vendor"],
            "total": float(row["amount"]),
            "percent": round(float(row["amount"]) / total * 100, 1) if total else 0,
        }
        for _, row in vendor_totals.iterrows()
    ]
