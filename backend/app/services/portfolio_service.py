"""Portfolio data service — wraps existing portfolio.py logic."""

import importlib.util
import types
from functools import lru_cache

import pandas as pd

from ..config import DATA_DIR, PORTFOLIO_ROOT

RETIREMENT_TYPES = {"401k", "Roth IRA", "Traditional IRA"}


def _load_portfolio_module():
    """Import the portfolio.py module from the data directory."""
    module_path = DATA_DIR / "portfolio.py"
    spec = importlib.util.spec_from_file_location("portfolio", str(module_path))
    mod = types.ModuleType("portfolio")
    mod.__file__ = str(module_path)
    spec.loader.exec_module(mod)
    return mod


def get_snapshots() -> list[str]:
    if not PORTFOLIO_ROOT.exists():
        return []
    return sorted(
        [d.name for d in PORTFOLIO_ROOT.iterdir()
         if d.is_dir() and d.name[:4].isdigit()],
        reverse=True,
    )


@lru_cache(maxsize=4)
def load_holdings(snapshot_name: str) -> pd.DataFrame:
    mod = _load_portfolio_module()
    snapshot_dir = PORTFOLIO_ROOT / snapshot_name
    inv_dir = snapshot_dir / "Investments&Balances"
    mod.DATA_DIR = inv_dir if inv_dir.exists() else snapshot_dir
    return mod.load_all_holdings()


def invalidate_cache():
    load_holdings.cache_clear()


def get_summary(snapshot_name: str) -> dict:
    holdings = load_holdings(snapshot_name)
    if holdings.empty:
        return {"total_value": 0, "snapshot": snapshot_name}
    total = float(holdings["value"].sum())
    return {"total_value": total, "snapshot": snapshot_name}


def get_asset_allocation(snapshot_name: str) -> list[dict]:
    holdings = load_holdings(snapshot_name)
    if holdings.empty:
        return []
    total = holdings["value"].sum()
    ac = holdings.groupby("asset_class")["value"].sum().sort_values(ascending=False)
    return [
        {
            "asset_class": name,
            "value": float(val),
            "percent": round(float(val) / total * 100, 1) if total else 0,
        }
        for name, val in ac.items()
    ]


def get_by_account(snapshot_name: str) -> list[dict]:
    holdings = load_holdings(snapshot_name)
    if holdings.empty:
        return []
    total = holdings["value"].sum()
    acct = holdings.groupby(["account", "account_type"]).agg(
        value=("value", "sum"),
        cost=("cost", "sum"),
        unrealized_gl=("unrealized_gl", "sum"),
    ).reset_index().sort_values("value", ascending=False)
    return [
        {
            "account": row["account"],
            "account_type": row["account_type"],
            "value": float(row["value"]),
            "cost": float(row["cost"]),
            "unrealized_gl": float(row["unrealized_gl"]),
            "gl_pct": round(float(row["unrealized_gl"]) / row["cost"] * 100, 1) if row["cost"] > 0 else 0,
            "pct_of_portfolio": round(float(row["value"]) / total * 100, 1) if total else 0,
        }
        for _, row in acct.iterrows()
    ]


def get_retirement_vs_taxable(snapshot_name: str) -> dict:
    holdings = load_holdings(snapshot_name)
    if holdings.empty:
        return {"rows": [], "retirement_total": 0, "taxable_total": 0, "total": 0}

    total = holdings["value"].sum()
    h = holdings.copy()
    h["tax_bucket"] = h["account_type"].apply(
        lambda t: "Retirement" if t in RETIREMENT_TYPES else "Taxable"
    )
    pivot = h.groupby(["asset_class", "tax_bucket"])["value"].sum().unstack(fill_value=0)
    for col in ["Retirement", "Taxable"]:
        if col not in pivot.columns:
            pivot[col] = 0
    pivot["Total"] = pivot["Retirement"] + pivot["Taxable"]
    pivot = pivot.sort_values("Total", ascending=False)

    ret_total = float(pivot["Retirement"].sum())
    tax_total = float(pivot["Taxable"].sum())

    rows = []
    for ac, row in pivot.iterrows():
        rows.append({
            "asset_class": ac,
            "retirement": float(row["Retirement"]),
            "pct_retirement": round(float(row["Retirement"]) / ret_total * 100, 1) if ret_total else 0,
            "taxable": float(row["Taxable"]),
            "pct_taxable": round(float(row["Taxable"]) / tax_total * 100, 1) if tax_total else 0,
            "total": float(row["Total"]),
            "pct_portfolio": round(float(row["Total"]) / total * 100, 1) if total else 0,
        })

    return {
        "rows": rows,
        "retirement_total": ret_total,
        "taxable_total": tax_total,
        "total": float(total),
    }


def get_comparison(current: str, previous: str) -> dict:
    cur_holdings = load_holdings(current)
    old_holdings = load_holdings(previous)

    if cur_holdings.empty or old_holdings.empty:
        return {"error": "One or both snapshots have no data"}

    cur_total = float(cur_holdings["value"].sum())
    old_total = float(old_holdings["value"].sum())
    change = cur_total - old_total
    pct_change = round(change / old_total * 100, 1) if old_total else 0

    old_ac = old_holdings.groupby("asset_class")["value"].sum().rename("previous")
    new_ac = cur_holdings.groupby("asset_class")["value"].sum().rename("current")
    comp = pd.concat([old_ac, new_ac], axis=1).fillna(0)
    comp["change"] = comp["current"] - comp["previous"]
    comp["change_pct"] = ((comp["change"] / comp["previous"]) * 100).round(1)
    comp = comp.sort_values("current", ascending=False)

    by_asset_class = [
        {
            "asset_class": ac,
            "previous": float(row["previous"]),
            "current": float(row["current"]),
            "change": float(row["change"]),
            "change_pct": float(row["change_pct"]) if pd.notna(row["change_pct"]) else 0,
        }
        for ac, row in comp.iterrows()
    ]

    return {
        "current_snapshot": current,
        "previous_snapshot": previous,
        "current_total": cur_total,
        "previous_total": old_total,
        "change": change,
        "pct_change": pct_change,
        "by_asset_class": by_asset_class,
    }
