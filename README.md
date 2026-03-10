# Woffieta Finances

Personal finance tracker with cash flow analysis, investment portfolio tracking, and an interactive Streamlit dashboard.

## Features

- **Cash Flow Tracking** — Parses CSV exports from 11 bank/credit card accounts, classifies transactions by category, and generates monthly reports
- **Portfolio Analysis** — Reads holdings from 9 investment accounts, calculates asset allocation by account type (retirement vs taxable), and generates Excel reports
- **Interactive Dashboard** — Streamlit app with monthly expense/income charts, net income tracking, top vendors, and portfolio allocation views
- **File Upload** — Upload monthly CSV exports directly through the dashboard and run the pipeline with one click

## Project Structure

```
Woffieta Finances/
├── README.md
├── generate_demo_data.py        # Generates Demo/ folder with fake data
├── Production/                  # Real financial data & scripts
│   ├── cashflow.py              # Cash flow pipeline (parse, classify, export)
│   ├── generate_report.py       # Excel cash flow report generator
│   ├── portfolio.py             # Investment portfolio analyzer
│   ├── dashboard.py             # Streamlit dashboard
│   ├── Context.md               # Category rules documentation
│   ├── CashFlow/                # Transaction CSVs & reports
│   │   ├── 2025/                # Full-year CSV exports
│   │   ├── Jan26/, Feb26/...    # Monthly CSV exports
│   │   ├── Monthly/             # Pipeline output (monthly splits)
│   │   ├── all_transactions.csv # Combined transaction file
│   │   └── CashFlow_Report.xlsx # Excel report
│   └── InvestmentPortfolio/
│       ├── {date}/              # Dated snapshots
│       │   ├── Investments&Balances/  # Account CSV exports
│       │   └── Portfolio_Report.xlsx
│       └── Portfolio_Report.xlsx      # Latest report (top-level copy)
└── Demo/                        # Fake data for demonstrations
    ├── (same structure as Production)
    └── ...
```

## Supported Accounts

### Cash Flow (11 accounts)

| Account | Type | Parser |
|---------|------|--------|
| Aeroplan, AmazonPrime, United | Chase Credit Cards | Chase card format |
| VentureX, VentureOne | Capital One Credit Cards | Debit/Credit columns |
| Alaska | Bank of America Credit Card | BoA card format |
| SoFi Joint Checking/Savings | SoFi Bank | SoFi format |
| BoA Checking/Savings | Bank of America | Summary header format |
| Chase Checking | Chase Bank | Trailing-comma format |

### Portfolio (9 accounts)

| Account | Type | Parser |
|---------|------|--------|
| Chase Taxable Brokerage | Taxable | Chase 82-column |
| Chase Parametric | Taxable | Chase 82-column |
| Scott's Roth IRA | Roth IRA | Chase 82-column |
| Scott's Traditional IRA | Traditional IRA | Chase 82-column |
| SoFi Joint (managed) | Taxable | SoFi managed |
| SoFi Self-Directed | Taxable | SoFi brokerage |
| Maria's Roth IRA | Roth IRA | Vanguard brokerage |
| Maria Empower 401k | 401k | Investment/Balance |
| Maria Accrue LevelTen 401k | 401k | Vanguard fund |

## Quick Start

### Production

```bash
cd Production
python3 cashflow.py              # Parse transactions & classify
python3 generate_report.py       # Generate Excel cash flow report
python3 portfolio.py             # Generate portfolio report
python3 -m streamlit run dashboard.py  # Launch dashboard
```

### Demo (with fake data)

```bash
python3 generate_demo_data.py    # Generate Demo/ folder
cd Demo
python3 cashflow.py
python3 generate_report.py
python3 portfolio.py
python3 -m streamlit run dashboard.py
```

The demo generator creates 12 months of realistic fake transactions across all accounts with amounts scaled to 60% of typical values. Use `--scale` to adjust (e.g., `--scale 0.4` for 40%).

## Dashboard

The Streamlit dashboard has three tabs:

1. **Cash Flow** — Monthly expenses by category (stacked bar with hover breakdown), income by source, net income with cumulative trend, spending by category table, top 10 vendors
2. **Portfolio** — Asset allocation pie charts, retirement vs taxable breakdown with percentages, account-level views, snapshot comparison (when multiple snapshots exist)
3. **Upload & Run** — Upload monthly CSV exports per account, run the pipeline, and refresh the dashboard

## Requirements

- Python 3.9+
- pandas, openpyxl, streamlit, plotly

```bash
pip3 install pandas openpyxl streamlit plotly
```
