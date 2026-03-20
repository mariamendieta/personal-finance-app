"""Budget service — manage monthly budgets and compare against actuals."""

import json
from pathlib import Path

from ..config import DATA_DIR
from .cashflow_service import get_spending_by_category

BUDGETS_FILE: Path = DATA_DIR / "budgets.json"


def _read_budgets_file() -> dict:
    if BUDGETS_FILE.exists():
        return json.loads(BUDGETS_FILE.read_text())
    return {}


def _write_budgets_file(budgets: dict) -> None:
    BUDGETS_FILE.write_text(json.dumps(budgets, indent=2) + "\n")


def get_budgets() -> dict:
    """Return the current budgets dict {category: monthly_amount}."""
    return _read_budgets_file()


def set_budgets(budgets: dict) -> dict:
    """Save budgets to file and return the saved dict."""
    _write_budgets_file(budgets)
    return budgets


def get_budget_vs_actual(months: int = 1) -> dict:
    """Compare budgeted amounts against actual spending.

    Returns per-category breakdown and a summary.
    """
    budgets = get_budgets()

    # Actual spending for the selected period
    actual_data = get_spending_by_category(months)
    actual_by_cat = {row["category"]: row["total"] for row in actual_data}

    # 12-month data for averages
    twelve_mo_data = get_spending_by_category(12)
    twelve_mo_by_cat = {row["category"]: row["total"] for row in twelve_mo_data}

    categories = []
    total_budget_for_period = 0.0
    total_actual = 0.0
    categories_over = 0
    categories_under = 0

    for category, monthly_budget in sorted(budgets.items()):
        budget_for_period = monthly_budget * months
        actual_spent = actual_by_cat.get(category, 0.0)
        difference = budget_for_period - actual_spent
        avg_12mo = twelve_mo_by_cat.get(category, 0.0) / 12

        total_budget_for_period += budget_for_period
        total_actual += actual_spent

        if difference >= 0:
            categories_under += 1
        else:
            categories_over += 1

        categories.append({
            "category": category,
            "monthly_budget": monthly_budget,
            "actual_spent": round(actual_spent, 2),
            "budget_for_period": round(budget_for_period, 2),
            "difference": round(difference, 2),
            "avg_12mo": round(avg_12mo, 2),
        })

    total_difference = total_budget_for_period - total_actual
    pct_used = round(total_actual / total_budget_for_period * 100, 1) if total_budget_for_period else 0.0

    return {
        "months": months,
        "categories": categories,
        "summary": {
            "total_budget_for_period": round(total_budget_for_period, 2),
            "total_actual": round(total_actual, 2),
            "total_difference": round(total_difference, 2),
            "pct_used": pct_used,
            "categories_over": categories_over,
            "categories_under": categories_under,
        },
    }


def get_available_categories() -> list[str]:
    """Return all spending categories found in cashflow data (12-month window)."""
    data = get_spending_by_category(12)
    return sorted(row["category"] for row in data)
