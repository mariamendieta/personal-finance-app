"""Chat service — answers financial questions by querying local data. No API key needed."""

import re

from .cashflow_service import (
    get_summary as cf_summary,
    get_spending_by_category,
    get_top_vendors,
    get_monthly_income,
    get_net_income,
)
from .portfolio_service import (
    get_snapshots,
    get_summary as pf_summary,
    get_asset_allocation,
    get_retirement_vs_taxable,
    get_by_account,
)


def _fmt(val: float, decimals: int = 0) -> str:
    if decimals == 0:
        return f"${val:,.0f}"
    return f"${val:,.{decimals}f}"


def _match(text: str, *patterns: str) -> bool:
    t = text.lower()
    return any(p in t for p in patterns)


def get_chat_response(messages: list[dict]) -> str:
    """Parse the latest user message and return a data-driven answer."""
    if not messages:
        return "Ask me anything about your finances!"

    question = messages[-1].get("content", "").strip()
    if not question:
        return "I didn't catch that. Try asking about your spending, income, or investments."

    q = question.lower()

    # ── Summary / Overview ──
    if _match(q, "summary", "overview", "how am i doing", "financial health", "big picture", "snapshot"):
        cf = cf_summary(12)
        lines = [
            "**Cash Flow (Last 12 Months)**",
            f"- Total Income: {_fmt(cf['total_income'])}",
            f"- Total Spending: {_fmt(cf['total_spending'])}",
            f"- Net Income: {_fmt(cf['net_income'])}",
        ]
        snapshots = get_snapshots()
        if snapshots:
            pf = pf_summary(snapshots[0])
            lines.append(f"\n**Investment Portfolio ({snapshots[0]})**")
            lines.append(f"- Total Value: {_fmt(pf['total_value'], 2)}")
        return "\n".join(lines)

    # ── Spending by category ──
    if _match(q, "spending", "expense", "spend", "biggest expense", "where does my money go",
              "category", "categories", "breakdown"):
        # Check if asking about a specific category
        categories = get_spending_by_category(12)
        if not categories:
            return "No spending data found."

        # Check for specific category mention
        for cat in categories:
            if cat["category"].lower() in q:
                return f"**{cat['category']}** (Last 12 months): {_fmt(cat['total'], 2)} — {cat['percent']}% of total spending."

        lines = ["**Spending by Category (Last 12 Months)**", ""]
        for c in categories[:15]:
            bar = "█" * max(1, int(c["percent"] / 3))
            lines.append(f"{bar} **{c['category']}**: {_fmt(c['total'])} ({c['percent']}%)")
        total = sum(c["total"] for c in categories)
        lines.append(f"\n**Total Spending**: {_fmt(total)}")
        return "\n".join(lines)

    # ── Top vendors ──
    if _match(q, "vendor", "merchant", "store", "who do i pay", "top vendor", "where do i shop"):
        vendors = get_top_vendors(12, 10)
        if not vendors:
            return "No vendor data found."
        lines = ["**Top 10 Vendors (Last 12 Months)**", ""]
        for i, v in enumerate(vendors, 1):
            lines.append(f"{i}. **{v['vendor']}**: {_fmt(v['total'])} ({v['percent']}%)")
        return "\n".join(lines)

    # ── Income ──
    if _match(q, "income", "earn", "salary", "paycheck", "revenue", "how much do i make"):
        cf = cf_summary(12)
        income_data = get_monthly_income(12)
        inc_totals: dict[str, float] = {}
        for item in income_data:
            inc_totals[item["subcategory"]] = inc_totals.get(item["subcategory"], 0) + item["amount"]

        lines = [
            f"**Total Income (Last 12 Months)**: {_fmt(cf['total_income'])}",
            "",
            "**By Source:**",
        ]
        for src, total in sorted(inc_totals.items(), key=lambda x: -x[1]):
            lines.append(f"- **{src}**: {_fmt(total)}")
        return "\n".join(lines)

    # ── Net income / savings ──
    if _match(q, "net income", "net", "saving", "save enough", "surplus", "deficit", "profit"):
        net_data = get_net_income(12)
        if not net_data:
            return "No data available."

        positive_months = sum(1 for m in net_data if m["net"] > 0)
        negative_months = sum(1 for m in net_data if m["net"] < 0)
        cumulative = net_data[-1]["cumulative"]

        lines = [
            "**Net Income (Last 12 Months)**",
            "",
        ]
        for m in net_data:
            month_label = m["month"][:7]
            sign = "+" if m["net"] >= 0 else ""
            indicator = "🟢" if m["net"] >= 0 else "🔴"
            lines.append(f"{indicator} **{month_label}**: {sign}{_fmt(m['net'])}")

        lines.append(f"\n**Cumulative**: {_fmt(cumulative)}")
        lines.append(f"Positive months: {positive_months} | Negative months: {negative_months}")
        return "\n".join(lines)

    # ── Monthly trend ──
    if _match(q, "month", "trend", "monthly", "over time", "each month"):
        net_data = get_net_income(12)
        if not net_data:
            return "No monthly data available."

        lines = ["**Monthly Breakdown (Last 12 Months)**", ""]
        lines.append("Month | Income | Spending | Net")
        lines.append("--- | --- | --- | ---")
        for m in net_data:
            month_label = m["month"][:7]
            lines.append(f"{month_label} | {_fmt(m['income'])} | {_fmt(m['spending'])} | {_fmt(m['net'])}")
        return "\n".join(lines)

    # ── Portfolio / investments ──
    if _match(q, "portfolio", "investment", "invest", "stock", "bond", "asset", "allocation",
              "retirement", "401k", "ira", "roth", "brokerage"):

        snapshots = get_snapshots()
        if not snapshots:
            return "No portfolio data found. Upload investment data in the Add Data tab."

        latest = snapshots[0]
        pf = pf_summary(latest)

        # Retirement vs taxable
        if _match(q, "retirement", "taxable", "401k", "ira", "roth", "tax"):
            ret_tax = get_retirement_vs_taxable(latest)
            if not ret_tax or not ret_tax["rows"]:
                return "No retirement/taxable breakdown available."

            lines = [
                f"**Retirement vs Taxable ({latest})**",
                "",
                f"- **Retirement**: {_fmt(ret_tax['retirement_total'])}",
                f"- **Taxable**: {_fmt(ret_tax['taxable_total'])}",
                f"- **Total**: {_fmt(ret_tax['total'])}",
                "",
                "**By Asset Class:**",
            ]
            for row in ret_tax["rows"]:
                lines.append(f"- {row['asset_class']}: Ret {_fmt(row['retirement'])} ({row['pct_retirement']}%) | Tax {_fmt(row['taxable'])} ({row['pct_taxable']}%)")
            return "\n".join(lines)

        # Account breakdown
        if _match(q, "account", "brokerage", "which account"):
            accounts = get_by_account(latest)
            if not accounts:
                return "No account data available."
            lines = [f"**Accounts ({latest})**", ""]
            for a in accounts:
                gl_str = ""
                if a["cost"] > 0:
                    sign = "+" if a["unrealized_gl"] >= 0 else ""
                    gl_str = f" | G/L: {sign}{_fmt(a['unrealized_gl'])} ({a['gl_pct']}%)"
                lines.append(f"- **{a['account']}** ({a['account_type']}): {_fmt(a['value'])}{gl_str}")
            lines.append(f"\n**Total**: {_fmt(pf['total_value'], 2)}")
            return "\n".join(lines)

        # Asset allocation (default for portfolio questions)
        allocation = get_asset_allocation(latest)
        lines = [
            f"**Portfolio ({latest})**",
            f"Total Value: {_fmt(pf['total_value'], 2)}",
            "",
            "**Asset Allocation:**",
        ]
        for a in allocation:
            bar = "█" * max(1, int(a["percent"] / 5))
            lines.append(f"{bar} **{a['asset_class']}**: {_fmt(a['value'])} ({a['percent']}%)")
        return "\n".join(lines)

    # ── Travel ──
    if _match(q, "travel"):
        categories = get_spending_by_category(12)
        travel = next((c for c in categories if c["category"] == "Travel"), None)
        if travel:
            return f"**Travel Spending (Last 12 Months)**: {_fmt(travel['total'], 2)} — {travel['percent']}% of total spending."
        return "No travel spending found in the last 12 months."

    # ── Childcare ──
    if _match(q, "childcare", "daycare", "kids", "child"):
        categories = get_spending_by_category(12)
        childcare = next((c for c in categories if c["category"] == "Childcare"), None)
        if childcare:
            return f"**Childcare Spending (Last 12 Months)**: {_fmt(childcare['total'], 2)} — {childcare['percent']}% of total spending."
        return "No childcare spending found in the last 12 months."

    # ── Groceries / food ──
    if _match(q, "grocery", "groceries", "food", "restaurant", "eating", "dining"):
        categories = get_spending_by_category(12)
        food_cats = [c for c in categories if c["category"] in ("Groceries", "Restaurants")]
        if food_cats:
            lines = ["**Food Spending (Last 12 Months)**", ""]
            total = 0
            for c in food_cats:
                lines.append(f"- **{c['category']}**: {_fmt(c['total'], 2)} ({c['percent']}%)")
                total += c["total"]
            lines.append(f"\n**Combined**: {_fmt(total)}")
            return "\n".join(lines)
        return "No food/grocery spending found."

    # ── Subscriptions ──
    if _match(q, "subscription", "recurring", "monthly charge"):
        categories = get_spending_by_category(12)
        subs = next((c for c in categories if c["category"] == "Subscriptions"), None)
        if subs:
            return f"**Subscriptions (Last 12 Months)**: {_fmt(subs['total'], 2)} — {subs['percent']}% of total spending.\n\nThat's about {_fmt(subs['total'] / 12, 2)}/month on average."
        return "No subscription spending found."

    # ── Mortgage / housing ──
    if _match(q, "mortgage", "housing", "house", "home", "rent", "loan"):
        categories = get_spending_by_category(12)
        housing_cats = [c for c in categories if c["category"] in ("Mortgage & Student Loans", "House & Maintenance", "Utilities")]
        if housing_cats:
            lines = ["**Housing Costs (Last 12 Months)**", ""]
            total = 0
            for c in housing_cats:
                lines.append(f"- **{c['category']}**: {_fmt(c['total'], 2)} ({c['percent']}%)")
                total += c["total"]
            lines.append(f"\n**Combined**: {_fmt(total)}")
            return "\n".join(lines)
        return "No housing costs found."

    # ── Car / transportation ──
    if _match(q, "car", "auto", "vehicle", "gas", "transportation", "uber", "lyft"):
        categories = get_spending_by_category(12)
        car = next((c for c in categories if c["category"] == "Car"), None)
        if car:
            return f"**Car Expenses (Last 12 Months)**: {_fmt(car['total'], 2)} — {car['percent']}% of total spending.\n\nThat's about {_fmt(car['total'] / 12, 2)}/month on average."
        return "No car expenses found."

    # ── Specific category search ──
    categories = get_spending_by_category(12)
    for cat in categories:
        if cat["category"].lower() in q or any(word in cat["category"].lower() for word in q.split() if len(word) > 3):
            return f"**{cat['category']}** (Last 12 months): {_fmt(cat['total'], 2)} — {cat['percent']}% of total spending.\n\nMonthly average: {_fmt(cat['total'] / 12, 2)}"

    # ── Fallback ──
    return (
        "I can answer questions about your finances! Try asking:\n\n"
        "- **\"Show me a summary\"** — overall financial health\n"
        "- **\"What are my biggest expenses?\"** — spending breakdown\n"
        "- **\"Top vendors\"** — where you spend the most\n"
        "- **\"How much do I earn?\"** — income by source\n"
        "- **\"Am I saving enough?\"** — net income trends\n"
        "- **\"Monthly breakdown\"** — month-by-month data\n"
        "- **\"Portfolio allocation\"** — investment breakdown\n"
        "- **\"Retirement vs taxable\"** — portfolio tax breakdown\n"
        "- Or ask about specific categories: travel, childcare, groceries, subscriptions, housing, car..."
    )
