"""
Woffieta Finances — Monthly Finance Dashboard
Run with: python3 -m streamlit run dashboard.py
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

# ── Paths ────────────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent
CASHFLOW_MONTHLY = BASE / "CashFlow" / "Monthly"
PORTFOLIO_ROOT = BASE / "InvestmentPortfolio"

# ── Family name (detect demo vs production) ──────────────────────────────────
IS_DEMO = "Demo" in str(BASE)
FAMILY_NAME = "Viviana and Michael" if IS_DEMO else "Woffieta Family"

# ── Account type buckets ─────────────────────────────────────────────────────
RETIREMENT_TYPES = {"401k", "Roth IRA", "Traditional IRA"}

# ── Brand colors ─────────────────────────────────────────────────────────────
BRAND = {
    "white": "#FFFFFF",
    "cool_white": "#F7F7F7",
    "warm_charcoal": "#2A2522",
    "stone": "#6B5E52",
    "cool_gray": "#E8E8E8",
    "mid_gray": "#9A9A9A",
    "verde_hoja": "#2D6A4F",
    "verde_claro": "#52B788",
    "coral": "#E07A5F",
    "marigold": "#E9A820",
    "azul": "#1B4965",
}

BRAND_PALETTE = [BRAND["azul"], BRAND["verde_hoja"], BRAND["verde_claro"], BRAND["coral"],
                 BRAND["marigold"], BRAND["stone"]]

# Bird of paradise SVG (from brand guidelines)
FLOWER_SVG = """<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" width="48" height="56"><path d="M60 140 C58 120, 52 105, 48 95" stroke="#2D6A4F" stroke-width="0.7" fill="none"/><path d="M28 96 C32 92, 48 88, 68 95 C72 96, 74 97, 72 99 C66 102, 40 102, 28 96Z" fill="#2D6A4F"/><polygon points="42,92 18,42 26,40" fill="#E9A820"/><polygon points="46,90 30,35 38,32" fill="#E9A820"/><polygon points="50,88 40,28 48,26" fill="#E07A5F"/><polygon points="54,87 48,22 56,20" fill="#E07A5F"/><polygon points="58,86 56,16 64,15" fill="#C9184A"/><polygon points="62,87 66,24 72,26" fill="#C9184A"/><path d="M50 92 C48 82, 44 72, 38 58 C36 54, 38 52, 42 54 C50 60, 56 78, 56 92Z" fill="#1B4965"/></svg>"""

FLOWER_SVG_SMALL = """<svg viewBox="0 0 120 140" xmlns="http://www.w3.org/2000/svg" width="40" height="48"><path d="M60 140 C58 120, 52 105, 48 95" stroke="#2D6A4F" stroke-width="0.7" fill="none"/><path d="M28 96 C32 92, 48 88, 68 95 C72 96, 74 97, 72 99 C66 102, 40 102, 28 96Z" fill="#2D6A4F"/><polygon points="42,92 18,42 26,40" fill="#E9A820"/><polygon points="46,90 30,35 38,32" fill="#E9A820"/><polygon points="50,88 40,28 48,26" fill="#E07A5F"/><polygon points="54,87 48,22 56,20" fill="#E07A5F"/><polygon points="58,86 56,16 64,15" fill="#C9184A"/><polygon points="62,87 66,24 72,26" fill="#C9184A"/><path d="M50 92 C48 82, 44 72, 38 58 C36 54, 38 52, 42 54 C50 60, 56 78, 56 92Z" fill="#1B4965"/></svg>"""

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Viviana and Michael — Finances", layout="wide")

# ── Brand CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=Lora:wght@400;500&family=Source+Sans+3:wght@300;400;500;600;700&display=swap');

/* Main app background */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #FFFFFF !important;
}
.main .block-container {
    background-color: #FFFFFF;
}

/* Sidebar styling */
section[data-testid="stSidebar"] {
    background-color: #F7F7F7 !important;
    border-right: 3px solid;
    border-image: linear-gradient(180deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1;
}
/* Push sidebar content to very top */
section[data-testid="stSidebar"] > div,
section[data-testid="stSidebar"] > div > div,
section[data-testid="stSidebar"] [data-testid="stSidebarContent"],
section[data-testid="stSidebar"] .stAppViewBlockContainer {
    padding-top: 0 !important;
    margin-top: 0 !important;
}
/* Hide the default sidebar close/collapse button area spacing */
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    padding: 0 !important;
    min-height: 0 !important;
    height: 0 !important;
}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    color: #6B5E52 !important;
}

/* Sidebar nav links */
.sidebar-nav a {
    display: block;
    font-family: 'Lora', serif;
    font-size: 1rem;
    font-weight: 400;
    color: #6B5E52;
    text-decoration: none;
    padding: 8px 16px;
    margin-bottom: 4px;
}
.sidebar-nav a:hover {
    color: #1B4965;
}
.sidebar-nav a.active {
    font-weight: 600;
    color: #1B4965;
    border-bottom: 2px solid #1B4965;
}

/* All text defaults */
.stApp, .stApp p, .stApp span, .stApp li, .stApp td, .stApp th {
    font-family: 'Source Sans 3', sans-serif !important;
    color: #2A2522 !important;
}

/* Headings */
.stApp h1, .stApp h2, .stApp h3 {
    font-family: 'Lora', serif !important;
    color: #2A2522 !important;
}

/* Tab styling — minimal underline style */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent !important;
    border-radius: 0 !important;
    padding: 0 !important;
    border-bottom: 1px solid #E8E8E8;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Lora', serif !important;
    font-size: 0.95rem !important;
    font-weight: 400;
    color: #6B5E52 !important;
    background-color: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    padding: 8px 20px !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #1B4965 !important;
    background-color: transparent !important;
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    border-radius: 0 !important;
    color: #1B4965 !important;
    font-weight: 600;
    border-bottom: 2px solid #1B4965 !important;
}
/* Remove the default Streamlit tab highlight bar */
.stTabs [data-baseweb="tab-highlight"] {
    display: none !important;
}
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

/* Metric cards */
[data-testid="stMetric"] {
    background-color: #F7F7F7;
    border-radius: 10px;
    padding: 16px 20px;
    border-left: 4px solid #1B4965;
}
[data-testid="stMetricLabel"] {
    font-family: 'Source Sans 3', sans-serif !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-size: 0.8rem !important;
    color: #6B5E52 !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Cormorant Garamond', serif !important;
    font-weight: 600;
    color: #2A2522 !important;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

/* Buttons */
.stButton > button[kind="primary"] {
    background-color: #1B4965 !important;
    color: #FFFFFF !important;
    border: none;
    font-family: 'Source Sans 3', sans-serif !important;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    background-color: #52B788 !important;
}

/* Dividers */
hr {
    border-color: #E8E8E8 !important;
}

/* Selectbox and inputs */
.stSelectbox label, .stCheckbox label, .stRadio label {
    font-family: 'Source Sans 3', sans-serif !important;
    color: #6B5E52 !important;
}
.stSelectbox [data-baseweb="select"] span {
    color: #2A2522 !important;
    font-weight: 500 !important;
}
.stSelectbox [data-baseweb="select"] {
    border-color: #6B5E52 !important;
}

/* Header bar accent */
.brand-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding-bottom: 8px;
    margin-bottom: 0.5rem;
    border-bottom: 3px solid;
    border-image: linear-gradient(90deg, #1B4965 0%, #2D6A4F 50%, #52B788 100%) 1;
}
.brand-header h1 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 2.4rem !important;
    font-weight: 400 !important;
    color: #2A2522 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.1 !important;
}
.brand-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.85rem;
    font-weight: 300;
    color: #6B5E52;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Sidebar header — flush to top */
.sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 1rem 0.5rem 0.75rem 0.5rem;
    margin: 0;
    border-bottom: 2px solid #1B4965;
    margin-bottom: 1.5rem;
}
.sidebar-brand svg {
    width: 44px;
    height: 52px;
    flex-shrink: 0;
}
.sidebar-brand-text h2 {
    font-family: 'Cormorant Garamond', serif !important;
    font-size: 1.15rem !important;
    font-weight: 500 !important;
    color: #2A2522 !important;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.15 !important;
}
.sidebar-brand-text .sidebar-subtitle {
    font-family: 'Source Sans 3', sans-serif;
    font-size: 0.7rem;
    font-weight: 300;
    color: #6B5E52;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin: 2px 0 0 0;
    padding: 0;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════════

section = st.query_params.get("section", "cashflow")
if section not in ("cashflow", "investments"):
    section = "cashflow"

with st.sidebar:
    st.markdown(f"""<div class="sidebar-brand">{FLOWER_SVG_SMALL}<div class="sidebar-brand-text"><h2>Viviana and Michael</h2><div class="sidebar-subtitle">Personal Finances</div></div></div>""", unsafe_allow_html=True)

    cf_cls = "active" if section == "cashflow" else ""
    inv_cls = "active" if section == "investments" else ""
    st.markdown(f"""
    <div class="sidebar-nav">
        <a href="?section=cashflow" target="_self" class="{cf_cls}">Cash Flow</a>
        <a href="?section=investments" target="_self" class="{inv_cls}">Investments</a>
    </div>
    """, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
section_label = "Cash Flow" if section == "cashflow" else "Investments"
st.markdown(f"""
<div class="brand-header">
    <div>
        <h1>{FAMILY_NAME}</h1>
        <div class="brand-subtitle">{section_label}</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def load_cashflow() -> pd.DataFrame:
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


@st.cache_data
def load_portfolio(snapshot_name: str) -> pd.DataFrame:
    """Load portfolio holdings from a snapshot by importing portfolio.py parsers."""
    import importlib.util, types

    spec = importlib.util.spec_from_file_location("portfolio", str(BASE / "portfolio.py"))
    mod = types.ModuleType("portfolio")
    mod.__file__ = str(BASE / "portfolio.py")
    spec.loader.exec_module(mod)

    snapshot_dir = PORTFOLIO_ROOT / snapshot_name
    inv_dir = snapshot_dir / "Investments&Balances"
    mod.DATA_DIR = inv_dir if inv_dir.exists() else snapshot_dir
    return mod.load_all_holdings()


def get_snapshots() -> list[str]:
    """List available portfolio snapshot dates."""
    if not PORTFOLIO_ROOT.exists():
        return []
    return sorted(
        [d.name for d in PORTFOLIO_ROOT.iterdir()
         if d.is_dir() and d.name[:4].isdigit()],
        reverse=True,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# CASH FLOW SECTION
# ═══════════════════════════════════════════════════════════════════════════════

if section == "cashflow":
    tab_dashboard, tab_add = st.tabs(["Dashboard", "Add Data"])

    # ── Load data ─────────────────────────────────────────────────────────────
    cf = load_cashflow()

    if cf.empty:
        with tab_dashboard:
            st.warning("No cash flow data found. Run cashflow.py first or upload data in the Add Data tab.")
    else:
        # Filter to last 12 months
        latest_month = cf["month"].max()
        twelve_months_ago = (latest_month - 11).to_timestamp()
        cf12 = cf[cf["month_dt"] >= twelve_months_ago].copy()

        spending = cf12[cf12["flow_type"] == "spending"].copy()
        income = cf12[cf12["flow_type"] == "income"].copy()
        all_months = sorted(cf12["month_dt"].unique())

        with tab_dashboard:
            # ── KPI row ───────────────────────────────────────────────────────
            total_income = income["amount"].sum()
            total_spending = spending["amount"].abs().sum()
            net = total_income - total_spending

            k1, k2, k3 = st.columns(3)
            k1.metric("Total Income (12 mo)", f"${total_income:,.0f}")
            k2.metric("Total Spending (12 mo)", f"${total_spending:,.0f}")
            k3.metric("Net Income (12 mo)", f"${net:,.0f}",
                      delta_color="normal" if net >= 0 else "inverse")

            st.divider()

            # ── Monthly Expenses by Category ──────────────────────────────────
            st.subheader("Monthly Expenses by Category")

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

            def map_display_category(cat):
                if cat in KEEP_CATEGORIES:
                    return cat
                if cat in DEBT_MERGE:
                    return "Mortgage, Loans & Car"
                if cat in OTHER_MERGE:
                    return "Other Expenses"
                return "Other Expenses"

            spending["display_category"] = spending["category"].apply(map_display_category)

            exp_detail = (
                spending.groupby(["month_dt", "display_category", "category"])["amount"]
                .sum().abs().reset_index()
            )

            hover_lines = (
                exp_detail.groupby(["month_dt", "display_category"], group_keys=False)
                .apply(lambda g: "<br>".join(
                    f"  {row['category']}: ${row['amount']:,.0f}"
                    for _, row in g.sort_values("amount", ascending=False).iterrows()
                ), include_groups=False)
                .reset_index(name="breakdown")
            )

            exp_by_cat = (
                exp_detail.groupby(["month_dt", "display_category"])["amount"]
                .sum().reset_index()
            )
            exp_by_cat = exp_by_cat.merge(hover_lines, on=["month_dt", "display_category"])
            exp_by_cat["hover"] = (
                "<b>" + exp_by_cat["display_category"] + "</b>: $"
                + exp_by_cat["amount"].apply(lambda x: f"{x:,.0f}")
                + "<br>" + exp_by_cat["breakdown"]
            )

            CATEGORY_COLORS = {
                "Mortgage, Loans & Car": BRAND["azul"],
                "Childcare": BRAND["verde_hoja"],
                "Taxes & Tax Fees": BRAND["coral"],
                "Travel": BRAND["coral"],
                "Other Expenses": BRAND["stone"],
                "Utilities": BRAND["marigold"],
                "House & Maintenance": BRAND["verde_claro"],
                "Subscriptions": BRAND["mid_gray"],
            }

            fig_exp = go.Figure()
            for cat in ["Mortgage, Loans & Car", "Childcare", "Taxes & Tax Fees", "Travel",
                        "Other Expenses", "Utilities", "House & Maintenance", "Subscriptions"]:
                mask = exp_by_cat["display_category"] == cat
                if not mask.any():
                    continue
                subset = exp_by_cat[mask]
                fig_exp.add_trace(go.Bar(
                    x=subset["month_dt"], y=subset["amount"],
                    name=cat,
                    marker_color=CATEGORY_COLORS.get(cat, "#999"),
                    hovertext=subset["hover"],
                    hoverinfo="text",
                ))

            monthly_totals = exp_by_cat.groupby("month_dt")["amount"].sum().reset_index()
            fig_exp.add_trace(go.Scatter(
                x=monthly_totals["month_dt"], y=monthly_totals["amount"],
                mode="text",
                text=monthly_totals["amount"].apply(lambda x: f"${x:,.0f}"),
                textposition="top center",
                textfont=dict(size=11, color="#333"),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig_exp.update_layout(
                barmode="stack", xaxis_tickformat="%b %Y",
                yaxis_title="Amount ($)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=450,
            )
            st.plotly_chart(fig_exp, use_container_width=True)

            # ── Monthly Income by Source ───────────────────────────────────────
            st.subheader("Monthly Income by Source")

            inc_by_src = (
                income.groupby(["month_dt", "subcategory"])["amount"]
                .sum().reset_index()
            )
            inc_by_src["subcategory"] = inc_by_src["subcategory"].fillna("Other Income")

            fig_inc = px.bar(
                inc_by_src, x="month_dt", y="amount", color="subcategory",
                labels={"month_dt": "", "amount": "Amount ($)", "subcategory": "Source"},
                color_discrete_sequence=[BRAND["azul"], BRAND["verde_hoja"], BRAND["verde_claro"], BRAND["coral"], BRAND["marigold"], BRAND["stone"]],
            )

            monthly_inc_totals = inc_by_src.groupby("month_dt")["amount"].sum().reset_index()
            fig_inc.add_trace(go.Scatter(
                x=monthly_inc_totals["month_dt"], y=monthly_inc_totals["amount"],
                mode="text",
                text=monthly_inc_totals["amount"].apply(lambda x: f"${x:,.0f}"),
                textposition="top center",
                textfont=dict(size=11, color="#333"),
                showlegend=False,
                hoverinfo="skip",
            ))

            fig_inc.update_layout(
                barmode="stack", xaxis_tickformat="%b %Y",
                yaxis_title="Amount ($)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=400,
            )
            st.plotly_chart(fig_inc, use_container_width=True)

            # ── Net Income per Month + Cumulative ─────────────────────────────
            st.subheader("Net Income per Month & Cumulative")

            monthly_income_s = income.groupby("month_dt")["amount"].sum()
            monthly_spending_s = spending.groupby("month_dt")["amount"].sum().abs()
            all_idx = pd.DatetimeIndex(all_months)
            monthly_income_s = monthly_income_s.reindex(all_idx, fill_value=0)
            monthly_spending_s = monthly_spending_s.reindex(all_idx, fill_value=0)
            monthly_net = monthly_income_s - monthly_spending_s
            cumulative_net = monthly_net.cumsum()

            net_df = pd.DataFrame({
                "month_dt": all_idx,
                "Net Income": monthly_net.values,
                "Cumulative": cumulative_net.values,
            })

            fig_net = go.Figure()
            colors = [BRAND["azul"] if v >= 0 else BRAND["coral"] for v in net_df["Net Income"]]
            fig_net.add_trace(go.Bar(
                x=net_df["month_dt"], y=net_df["Net Income"],
                name="Monthly Net", marker_color=colors,
            ))
            fig_net.add_trace(go.Scatter(
                x=net_df["month_dt"], y=net_df["Cumulative"],
                name="Cumulative", mode="lines+markers",
                line=dict(color=BRAND["azul"], width=3),
                yaxis="y2",
            ))
            fig_net.update_layout(
                yaxis=dict(title="Monthly Net ($)"),
                yaxis2=dict(title="Cumulative ($)", overlaying="y", side="right"),
                xaxis_tickformat="%b %Y",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=400,
            )
            st.plotly_chart(fig_net, use_container_width=True)

            # ── Time period filter for tables ─────────────────────────────────
            st.divider()
            last_month_label = latest_month.strftime("%B %Y")
            prev_month = latest_month - 1
            prev_month_label = prev_month.strftime("%B %Y")

            period_options = [
                last_month_label,
                prev_month_label,
                "Last 3 months",
                "Last 6 months",
                "Last 12 months",
            ]
            filter_col, _ = st.columns([1, 3])
            with filter_col:
                selected_period = st.selectbox("Time period", period_options, index=4, key="cf_period")

            if selected_period == last_month_label:
                spending_filtered = spending[spending["month"] == latest_month]
            elif selected_period == prev_month_label:
                spending_filtered = spending[spending["month"] == prev_month]
            else:
                n_months = {"Last 3 months": 3, "Last 6 months": 6, "Last 12 months": 12}[selected_period]
                period_cutoff = (latest_month - (n_months - 1)).to_timestamp()
                spending_filtered = spending[spending["month_dt"] >= period_cutoff]

            # ── Spending breakdown table ───────────────────────────────────────
            st.subheader(f"Spending by Category ({selected_period})")

            cat_totals = (
                spending_filtered.groupby("category")["amount"].sum().abs()
                .sort_values(ascending=False).reset_index()
            )
            cat_totals.columns = ["Category", "Total"]
            cat_totals["% of Spending"] = (cat_totals["Total"] / cat_totals["Total"].sum() * 100).round(1)
            cat_totals["Total"] = cat_totals["Total"].apply(lambda x: f"${x:,.2f}")
            cat_totals["% of Spending"] = cat_totals["% of Spending"].apply(lambda x: f"{x}%")
            st.dataframe(cat_totals, use_container_width=True, hide_index=True)

            # ── Top 10 Vendors ─────────────────────────────────────────────────
            st.subheader(f"Top 10 Vendors ({selected_period})")

            import re as _re

            VENDOR_RULES = [
                (_re.compile(r"JPMORGAN CHASE|JPMorgan Chase", _re.I), "JPMorgan Chase"),
                (_re.compile(r"WORLDKIDS", _re.I), "Worldkids School"),
                (_re.compile(r"IC\*.*COSTCO|IC\*.*INSTACAR|IC\* INSTACART|INSTACART", _re.I), "Instacart"),
                (_re.compile(r"COSTCO WHSE|COSTCO GAS", _re.I), "Costco"),
                (_re.compile(r"UBER\s+\*EATS", _re.I), "Uber Eats"),
                (_re.compile(r"UBER\s+\*TRIP", _re.I), "Uber Rides"),
                (_re.compile(r"^VENMO", _re.I), "Venmo"),
                (_re.compile(r"^Zelle", _re.I), "Zelle Payments"),
                (_re.compile(r"^PAYPAL", _re.I), "PayPal"),
                (_re.compile(r"TACA AIR", _re.I), "TACA Air"),
                (_re.compile(r"^IRS", _re.I), "IRS"),
                (_re.compile(r"T-MOBILE|TMOBILE", _re.I), "T-Mobile"),
                (_re.compile(r"PEMCO", _re.I), "Pemco Insurance"),
                (_re.compile(r"SEATTLEUTILTIES|SEATTLE UTIL", _re.I), "Seattle Utilities"),
                (_re.compile(r"MOHELA", _re.I), "Mohela"),
                (_re.compile(r"TARGET\s", _re.I), "Target"),
                (_re.compile(r"AMAZON|Amazon\.com|AMZN", _re.I), "Amazon"),
                (_re.compile(r"A ?B HOTELS", _re.I), "AB Hotels"),
                (_re.compile(r"NORBU THE MONTANNA", _re.I), "Norbu The Montanna"),
                (_re.compile(r"AIRBNB", _re.I), "Airbnb"),
                (_re.compile(r"VIDANTA", _re.I), "Vidanta"),
                (_re.compile(r"LINELEADER", _re.I), "LineLeader"),
                (_re.compile(r"YMCA", _re.I), "YMCA"),
                (_re.compile(r"SAFEWAY", _re.I), "Safeway"),
                (_re.compile(r"QFC", _re.I), "QFC"),
                (_re.compile(r"TRADER JOE", _re.I), "Trader Joe's"),
                (_re.compile(r"ORGANIC LIFE START", _re.I), "Organic Life Start"),
                (_re.compile(r"BANK OF AMERICA", _re.I), "Bank of America"),
                (_re.compile(r"COT\*FLT", _re.I), "COT*FLT (Flights)"),
                (_re.compile(r"VANGUARD BUY", _re.I), "Vanguard Buy"),
            ]

            def normalize_vendor(desc):
                for pattern, name in VENDOR_RULES:
                    if pattern.search(desc):
                        return name
                return desc

            spending_filtered["vendor"] = spending_filtered["description"].apply(normalize_vendor)

            total_spend_filtered = spending_filtered["amount"].abs().sum()
            vendor_totals = (
                spending_filtered.groupby("vendor")["amount"].sum().abs()
                .sort_values(ascending=False).head(10).reset_index()
            )
            vendor_totals.columns = ["Vendor", "Total"]
            vendor_totals = vendor_totals.reset_index(drop=True)
            vendor_totals["% of Spending"] = (vendor_totals["Total"] / total_spend_filtered * 100).round(1)

            fig_vendors = go.Figure(go.Bar(
                x=vendor_totals["Total"],
                y=vendor_totals["Vendor"],
                orientation="h",
                marker_color=BRAND["azul"],
                text=vendor_totals.apply(
                    lambda r: f"${r['Total']:,.0f} ({r['% of Spending']}%)", axis=1),
                textposition="auto",
            ))
            fig_vendors.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis_title="Amount ($)",
                height=400,
                margin=dict(l=250),
            )
            st.plotly_chart(fig_vendors, use_container_width=True)

    # ── Add Data tab (Cash Flow only) ─────────────────────────────────────────
    with tab_add:
        import subprocess, calendar
        from datetime import date as _date

        st.subheader("Upload Cash Flow Data")
        st.markdown("Upload your monthly CSV exports and run the cash flow pipeline.")

        # Month selector
        today = _date.today()
        month_options = []
        for offset in range(0, 6):
            m = today.month - offset
            y = today.year
            while m <= 0:
                m += 12
                y -= 1
            label = f"{calendar.month_abbr[m]} {y}"
            folder = f"{calendar.month_abbr[m]}{str(y)[-2:]}"
            month_options.append((label, folder, y))

        selected_label = st.selectbox("Select month", [m[0] for m in month_options])
        sel = next(m for m in month_options if m[0] == selected_label)
        month_folder = sel[1]

        st.divider()

        CASHFLOW_ROOT = BASE / "CashFlow"

        cc_col, bank_col = st.columns(2)

        CREDIT_CARDS = [
            ("Aeroplan (Chase)", "Aeroplan"),
            ("AmazonPrime (Chase)", "AmazonPrime"),
            ("United (Chase)", "United"),
            ("VentureX (Capital One)", "VentureX"),
            ("VentureOne (Capital One)", "VentureOne"),
            ("Alaska (BofA)", "Alaska"),
        ]
        BANK_ACCOUNTS = [
            ("SoFi Joint Checking", "SOFI-JointChecking"),
            ("SoFi Joint Savings", "SOFI-JointSavings"),
            ("BoA Checking", "BoA-Checking"),
            ("BoA Savings", "BoA-Savings"),
            ("Chase Checking", "Chase-Checking"),
        ]

        cf_dest = CASHFLOW_ROOT / month_folder
        cc_dir = cf_dest / "Credit Cards"
        bank_dir = cf_dest / "Checking and Savings"

        uploaded_cf_files = []

        with cc_col:
            st.markdown("**Credit Cards**")
            for display_name, file_prefix in CREDIT_CARDS:
                f = st.file_uploader(display_name, type=["csv"], key=f"cc_{file_prefix}")
                if f:
                    uploaded_cf_files.append((f, cc_dir, f"{file_prefix}_{month_folder}.csv"))

        with bank_col:
            st.markdown("**Checking & Savings**")
            for display_name, file_prefix in BANK_ACCOUNTS:
                f = st.file_uploader(display_name, type=["csv"], key=f"bank_{file_prefix}")
                if f:
                    uploaded_cf_files.append((f, bank_dir, f"{file_prefix}_{month_folder}.csv"))

        # Other cash flow files
        st.markdown("**Other Cash Flow Files**")
        st.caption("Upload any additional CSVs. Choose whether each goes to Credit Cards or Checking and Savings.")
        other_cf_files = st.file_uploader(
            "Additional cash flow CSVs", type=["csv"], accept_multiple_files=True, key="other_cf"
        )
        if other_cf_files:
            other_cf_type = st.radio(
                "Save these to:", ["Credit Cards", "Checking and Savings"], horizontal=True, key="other_cf_type"
            )
            other_cf_dir = cc_dir if other_cf_type == "Credit Cards" else bank_dir
            for f in other_cf_files:
                uploaded_cf_files.append((f, other_cf_dir, f.name))

        st.divider()

        # Run pipeline
        st.markdown("### Run Pipeline")
        cf_count = len(uploaded_cf_files)
        st.info(f"Ready: **{cf_count}** cash flow file(s)")

        if cf_dest.exists():
            existing = list(cf_dest.rglob("*.csv")) + list(cf_dest.rglob("*.CSV"))
            if existing:
                st.caption(f"Note: {month_folder}/ already has {len(existing)} file(s)")

        run_cashflow = st.checkbox("Run Cash Flow pipeline", value=cf_count > 0, key="cf_run_cf")
        run_report = st.checkbox("Generate Excel report", value=cf_count > 0, key="cf_run_rpt")

        if st.button("Save Files & Run", type="primary", disabled=(cf_count == 0), key="cf_run_btn"):
            progress = st.progress(0, text="Saving files...")

            for f, dest_dir, filename in uploaded_cf_files:
                dest_dir.mkdir(parents=True, exist_ok=True)
                (dest_dir / filename).write_bytes(f.read())
            st.success(f"Saved {cf_count} cash flow file(s) to `{month_folder}/`")

            progress.progress(30, text="Files saved.")

            results = []
            if run_cashflow:
                progress.progress(50, text="Running cashflow.py...")
                r = subprocess.run(
                    ["python3", str(BASE / "cashflow.py")],
                    capture_output=True, text=True, cwd=str(BASE),
                )
                if r.returncode == 0:
                    results.append(("cashflow.py", True, r.stdout[-500:]))
                else:
                    results.append(("cashflow.py", False, r.stderr[-500:]))

            if run_report:
                progress.progress(75, text="Running generate_report.py...")
                r = subprocess.run(
                    ["python3", str(BASE / "generate_report.py")],
                    capture_output=True, text=True, cwd=str(BASE),
                )
                if r.returncode == 0:
                    results.append(("generate_report.py", True, r.stdout[-500:]))
                else:
                    results.append(("generate_report.py", False, r.stderr[-500:]))

            progress.progress(100, text="Done!")

            for script, success, output in results:
                if success:
                    st.success(f"{script} completed")
                    with st.expander(f"{script} output"):
                        st.code(output)
                else:
                    st.error(f"{script} failed")
                    with st.expander(f"{script} error"):
                        st.code(output)

            st.cache_data.clear()
            st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# INVESTMENTS SECTION
# ═══════════════════════════════════════════════════════════════════════════════

elif section == "investments":
    tab_dashboard, tab_add = st.tabs(["Dashboard", "Add Data"])

    snapshots = get_snapshots()

    with tab_dashboard:
        if not snapshots:
            st.warning("No portfolio snapshots found. Upload data in the Add Data tab.")
        else:
            selected_snapshot = st.selectbox("Snapshot", snapshots)
            holdings = load_portfolio(selected_snapshot)

            if holdings.empty:
                st.warning("No holdings data in this snapshot.")
            else:
                total_value = holdings["value"].sum()
                st.metric("Total Portfolio Value", f"${total_value:,.2f}")
                st.divider()

                col1, col2 = st.columns(2)

                # ── Asset Class Allocation (Total) ────────────────────────────
                with col1:
                    st.subheader("Asset Class Allocation")
                    ac_totals = (
                        holdings.groupby("asset_class")["value"].sum()
                        .sort_values(ascending=False).reset_index()
                    )
                    fig_ac = px.pie(
                        ac_totals, values="value", names="asset_class",
                        color_discrete_sequence=BRAND_PALETTE,
                        hole=0.4,
                    )
                    fig_ac.update_traces(textposition="inside", textinfo="percent+label")
                    fig_ac.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_ac, use_container_width=True)

                # ── By Account ────────────────────────────────────────────────
                with col2:
                    st.subheader("By Account")
                    acct_totals = (
                        holdings.groupby("account")["value"].sum()
                        .sort_values(ascending=False).reset_index()
                    )
                    fig_acct = px.pie(
                        acct_totals, values="value", names="account",
                        color_discrete_sequence=[BRAND["azul"], BRAND["verde_hoja"], BRAND["verde_claro"], BRAND["coral"], BRAND["marigold"], BRAND["stone"]],
                        hole=0.4,
                    )
                    fig_acct.update_traces(textposition="inside", textinfo="percent+label")
                    fig_acct.update_layout(showlegend=False, height=400)
                    st.plotly_chart(fig_acct, use_container_width=True)

                st.divider()

                # ── Retirement vs Taxable ─────────────────────────────────────
                st.subheader("Asset Class: Retirement vs Taxable")

                holdings["tax_bucket"] = holdings["account_type"].apply(
                    lambda t: "Retirement" if t in RETIREMENT_TYPES else "Taxable"
                )

                pivot = (
                    holdings.groupby(["asset_class", "tax_bucket"])["value"]
                    .sum().unstack(fill_value=0)
                )
                for col in ["Retirement", "Taxable"]:
                    if col not in pivot.columns:
                        pivot[col] = 0
                pivot["Total"] = pivot["Retirement"] + pivot["Taxable"]
                pivot = pivot.sort_values("Total", ascending=False)

                ret_total = pivot["Retirement"].sum()
                tax_total = pivot["Taxable"].sum()
                pivot["% of Retirement"] = (pivot["Retirement"] / ret_total * 100).round(1) if ret_total else 0
                pivot["% of Taxable"] = (pivot["Taxable"] / tax_total * 100).round(1) if tax_total else 0
                pivot["% of Portfolio"] = (pivot["Total"] / total_value * 100).round(1)

                display_df = pivot[["Retirement", "% of Retirement", "Taxable", "% of Taxable", "Total", "% of Portfolio"]].copy()
                display_df.index.name = "Asset Class"
                st.dataframe(
                    display_df.style.format({
                        "Retirement": "${:,.0f}",
                        "Taxable": "${:,.0f}",
                        "Total": "${:,.0f}",
                        "% of Retirement": "{:.1f}%",
                        "% of Taxable": "{:.1f}%",
                        "% of Portfolio": "{:.1f}%",
                    }),
                    use_container_width=True,
                )

                # Side-by-side bar chart
                fig_rt = go.Figure()
                fig_rt.add_trace(go.Bar(
                    name="Retirement", x=pivot.index, y=pivot["Retirement"],
                    marker_color=BRAND["azul"],
                ))
                fig_rt.add_trace(go.Bar(
                    name="Taxable", x=pivot.index, y=pivot["Taxable"],
                    marker_color=BRAND["coral"],
                ))
                fig_rt.update_layout(
                    barmode="group", height=400,
                    yaxis_title="Value ($)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_rt, use_container_width=True)

                # ── Retirement vs Taxable allocation comparison ───────────────
                st.subheader("Allocation Comparison: Retirement vs Taxable")

                col_r, col_t = st.columns(2)
                with col_r:
                    st.markdown("**Retirement Accounts**")
                    ret_holdings = holdings[holdings["tax_bucket"] == "Retirement"]
                    ret_ac = ret_holdings.groupby("asset_class")["value"].sum().sort_values(ascending=False).reset_index()
                    fig_r = px.pie(ret_ac, values="value", names="asset_class",
                                  color_discrete_sequence=BRAND_PALETTE, hole=0.4)
                    fig_r.update_traces(textposition="inside", textinfo="percent+label")
                    fig_r.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig_r, use_container_width=True)

                with col_t:
                    st.markdown("**Taxable Accounts**")
                    tax_holdings = holdings[holdings["tax_bucket"] == "Taxable"]
                    tax_ac = tax_holdings.groupby("asset_class")["value"].sum().sort_values(ascending=False).reset_index()
                    fig_t = px.pie(tax_ac, values="value", names="asset_class",
                                  color_discrete_sequence=BRAND_PALETTE, hole=0.4)
                    fig_t.update_traces(textposition="inside", textinfo="percent+label")
                    fig_t.update_layout(showlegend=False, height=350)
                    st.plotly_chart(fig_t, use_container_width=True)

                # ── Snapshot comparison ────────────────────────────────────────
                if len(snapshots) > 1:
                    st.divider()
                    st.subheader("Portfolio Changes Over Time")

                    compare_to = st.selectbox("Compare to", snapshots[1:], key="compare")
                    old_holdings = load_portfolio(compare_to)

                    if not old_holdings.empty:
                        old_total = old_holdings["value"].sum()
                        change = total_value - old_total
                        pct_change = (change / old_total * 100) if old_total else 0

                        c1, c2, c3 = st.columns(3)
                        c1.metric(f"Value ({compare_to})", f"${old_total:,.0f}")
                        c2.metric(f"Value ({selected_snapshot})", f"${total_value:,.0f}")
                        c3.metric("Change", f"${change:,.0f}", f"{pct_change:+.1f}%")

                        old_ac = old_holdings.groupby("asset_class")["value"].sum().rename("Previous")
                        new_ac = holdings.groupby("asset_class")["value"].sum().rename("Current")
                        comp = pd.concat([old_ac, new_ac], axis=1).fillna(0)
                        comp["Change"] = comp["Current"] - comp["Previous"]
                        comp["Change %"] = ((comp["Change"] / comp["Previous"]) * 100).round(1)
                        comp = comp.sort_values("Current", ascending=False)

                        st.dataframe(
                            comp.style.format({
                                "Previous": "${:,.0f}",
                                "Current": "${:,.0f}",
                                "Change": "${:,.0f}",
                                "Change %": "{:+.1f}%",
                            }),
                            use_container_width=True,
                        )

                holdings.drop(columns=["tax_bucket"], inplace=True, errors="ignore")

    # ── Add Data tab (Investments only) ───────────────────────────────────────
    with tab_add:
        import subprocess
        from datetime import date as _date

        st.subheader("Upload Investment Data")
        st.markdown("Upload your portfolio CSV exports and run the portfolio analysis.")

        PORTFOLIO_FILES = [
            ("Chase Taxable Brokerage", "ChaseTaxableBrokerage.csv"),
            ("Chase Parametric", "ChaseParametric.csv"),
            ("Michael's Roth IRA (Chase)", "ScottsRothIRA_Chase.csv"),
            ("Michael's Traditional IRA", "ScottsTraditionalIRA.csv"),
            ("SoFi Joint", "SOFI_Joint.csv"),
            ("SoFi Self-Directed", "SOFI_SelfDirected.csv"),
            ("Viviana's Roth IRA", "Marias Roth IRA.csv"),
            ("Viviana 401k", "Viviana 401k.csv"),
            ("Viviana Secondary 401k", "Viviana Secondary 401k.csv"),
        ]

        today = _date.today()
        portfolio_date = today.strftime("%Y-%m-%d")
        portfolio_dest = PORTFOLIO_ROOT / portfolio_date / "Investments&Balances"
        uploaded_portfolio_files = []

        p_cols = st.columns(3)
        for i, (display_name, filename) in enumerate(PORTFOLIO_FILES):
            with p_cols[i % 3]:
                f = st.file_uploader(display_name, type=["csv"], key=f"port_{filename}")
                if f:
                    uploaded_portfolio_files.append((f, portfolio_dest, filename))

        # Other investment files
        st.markdown("**Other Investment Files**")
        st.caption("Upload any additional investment/balance CSVs (will be saved with their original filename).")
        other_pf_files = st.file_uploader(
            "Additional portfolio CSVs", type=["csv"], accept_multiple_files=True, key="other_pf"
        )
        for f in other_pf_files:
            uploaded_portfolio_files.append((f, portfolio_dest, f.name))

        st.divider()

        # Run pipeline
        st.markdown("### Run Pipeline")
        pf_count = len(uploaded_portfolio_files)
        st.info(f"Ready: **{pf_count}** portfolio file(s)")

        run_portfolio = st.checkbox("Run Portfolio analysis", value=pf_count > 0, key="inv_run_port")

        if st.button("Save Files & Run", type="primary", disabled=(pf_count == 0), key="inv_run_btn"):
            progress = st.progress(0, text="Saving files...")

            portfolio_dest.mkdir(parents=True, exist_ok=True)
            for f, dest_dir, filename in uploaded_portfolio_files:
                (dest_dir / filename).write_bytes(f.read())
            st.success(f"Saved {pf_count} portfolio file(s) to `{portfolio_date}/`")

            progress.progress(40, text="Files saved.")

            results = []
            if run_portfolio:
                progress.progress(70, text="Running portfolio.py...")
                r = subprocess.run(
                    ["python3", str(BASE / "portfolio.py")],
                    capture_output=True, text=True, cwd=str(BASE),
                )
                if r.returncode == 0:
                    results.append(("portfolio.py", True, r.stdout[-500:]))
                else:
                    results.append(("portfolio.py", False, r.stderr[-500:]))

            progress.progress(100, text="Done!")

            for script, success, output in results:
                if success:
                    st.success(f"{script} completed")
                    with st.expander(f"{script} output"):
                        st.code(output)
                else:
                    st.error(f"{script} failed")
                    with st.expander(f"{script} error"):
                        st.code(output)

            st.cache_data.clear()
            st.rerun()
