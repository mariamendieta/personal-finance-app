# Woffieta Finances

Personal finance tracker with cash flow analysis, investment portfolio tracking, and an interactive Streamlit dashboard.

## Features

- **Cash Flow Tracking** — Parses CSV exports from 11 bank/credit card accounts, classifies transactions by category, and generates monthly reports
- **Portfolio Analysis** — Reads holdings from 9 investment accounts, calculates asset allocation by account type (retirement vs taxable), and generates Excel reports
- **Interactive Dashboard** — Streamlit app with monthly expense/income charts, net income tracking, top vendors, and portfolio allocation views
- **File Upload** — Upload monthly CSV exports directly through the dashboard and run the pipeline with one click

## Repository Setup

This project uses **two repos** to separate code from private financial data:

| Repo | Contents | Who has access |
|------|----------|----------------|
| **woffieta-finances** | Python scripts, demo data, README, brand guidelines | Anyone you invite |
| **woffieta-data** | Real financial CSVs, Excel reports, Context.md | You + Scott only |

### First-time setup (full access — you & Scott)

```bash
# 1. Clone the code repo
git clone https://github.com/mariamendieta/woffieta-finances.git
cd woffieta-finances

# 2. Clone the data repo into Production/
cd Production
git clone https://github.com/mariamendieta/woffieta-data.git .

# 3. Run the dashboard
python3 -m streamlit run dashboard.py
```

> The `.` in step 2 clones the data directly into the `Production/` folder (alongside the scripts) rather than creating a subfolder.

### First-time setup (demo only — anyone else)

```bash
git clone https://github.com/mariamendieta/woffieta-finances.git
cd woffieta-finances/Demo
python3 -m streamlit run dashboard.py
```

They only see demo data with fake names and reduced amounts.

### Adding Scott as a collaborator

Go to https://github.com/mariamendieta/woffieta-data/settings/access and add Scott's GitHub username.

### Monthly update workflow

After downloading new CSV exports and running the pipelines:

```bash
# Commit & push data changes
cd Production
git add -A
git commit -m "March 2026 data"
git push

# Commit & push code changes (if scripts were modified)
cd ..
git add -A
git commit -m "Update dashboard"
git push
```

### Pulling latest changes

```bash
# Pull code updates
cd woffieta-finances
git pull

# Pull data updates
cd Production
git pull
```

## Project Structure

```
woffieta-finances/              ← code repo
├── README.md
├── .gitignore                  ← excludes Production data
├── generate_demo_data.py       ← generates Demo/ with fake data
├── BrandGuidelines/
├── Production/
│   ├── cashflow.py             ← cash flow pipeline
│   ├── generate_report.py      ← Excel report generator
│   ├── portfolio.py            ← portfolio analyzer
│   ├── dashboard.py            ← Streamlit dashboard
│   ├── CashFlow/               ← ⬇ from woffieta-data repo
│   ├── InvestmentPortfolio/    ← ⬇ from woffieta-data repo
│   └── Context.md              ← ⬇ from woffieta-data repo
└── Demo/                       ← demo data + script copies
    ├── (same structure as Production)
    └── UploadTest/             ← sample files for testing uploads
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

### Production (with real data)

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

The dashboard has a sidebar to switch between two sections:

- **Cash Flow** — Monthly expenses by category (stacked bar with hover breakdown), income by source, net income with cumulative trend, spending by category table, top 10 vendors. Add Data tab for uploading monthly CSVs.
- **Investments** — Asset allocation pie charts, retirement vs taxable breakdown with percentages, account-level views, snapshot comparison. Add Data tab for uploading portfolio CSVs.

## Requirements

- Python 3.9+
- pandas, openpyxl, streamlit, plotly

```bash
pip3 install pandas openpyxl streamlit plotly
```
