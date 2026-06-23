"""Application configuration."""

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_MODE = os.environ.get("DATA_MODE", "demo").lower()
if DATA_MODE not in ("demo", "production"):
    DATA_MODE = "demo"

# Production data is private and lives OUTSIDE this (public) repo. Point
# PRODUCTION_DATA_DIR at the local woffieta-data clone so no financial data
# ever enters the repo tree. Falls back to ./Production for the legacy
# clone-into-Production setup (which .gitignore also protects).
if DATA_MODE == "demo":
    DATA_DIR = PROJECT_ROOT / "Demo"
elif os.environ.get("PRODUCTION_DATA_DIR"):
    DATA_DIR = Path(os.environ["PRODUCTION_DATA_DIR"]).expanduser().resolve()
else:
    DATA_DIR = PROJECT_ROOT / "Production"
CASHFLOW_MONTHLY = DATA_DIR / "CashFlow" / "Monthly"
CASHFLOW_ROOT = DATA_DIR / "CashFlow"
PORTFOLIO_ROOT = DATA_DIR / "InvestmentPortfolio"

IS_DEMO = DATA_MODE == "demo"
FAMILY_NAME = "Viviana and Michael's Finances" if IS_DEMO else "Woffieta Family Finances"

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

BRAND_PALETTE = [BRAND["azul"], BRAND["verde_hoja"], BRAND["verde_claro"],
                 BRAND["coral"], BRAND["marigold"], BRAND["stone"]]
