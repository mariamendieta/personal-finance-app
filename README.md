# Personal Finance App

Personal finance tracker with cash flow analysis, investment portfolio tracking, and a web dashboard built with Next.js and FastAPI.

[View Architecture Deck](https://gamma.app/generations/O8Gs4v17UIWGKcx5k8Gjv)

## Features

- **Cash Flow Tracking** — Parses CSV exports from multiple bank/credit card accounts, classifies transactions by category, and generates monthly reports
- **Transaction Notes** — Add notes to individual transactions for context (reimbursable, trip details, etc.)
- **Category Drill-Down** — Click through categories → subcategories → vendors to explore spending
- **Income & Expense Filtering** — Toggle income sources and expense categories in/out of the net cash flow chart
- **Portfolio Analysis** — Reads holdings from investment accounts, calculates asset allocation, and generates reports
- **Action Items** — Track financial tasks with assignees, categories, and status
- **File Upload** — Upload monthly CSV exports through the app
- **Instructions Page** — Step-by-step guide for monthly updates

## Tech Stack

- **Frontend**: Next.js 15 + React + Tailwind CSS + Recharts
- **Backend**: FastAPI + Python
- **Data**: pandas for CSV processing, JSON for notes/config

## Quick Start (Demo Mode)

```bash
# 1. Clone the repo
git clone https://github.com/mariamendieta/personal-finance-app.git
cd personal-finance-app

# 2. Generate demo data
python3 generate_demo_data.py
cd Demo && python3 cashflow.py && cd ..

# 3. Install & start backend
pip3 install fastapi uvicorn pandas openpyxl
DATA_MODE=demo python3 -m uvicorn backend.app.main:app --port 8000 &

# 4. Install & start frontend
cd frontend && npm install && npm run dev -- -p 3001
```

Open http://localhost:3001

## Running with Your Own Data

This app supports a separate private data repo so you can keep your financial data private while sharing the app code.

### Setup with private data repo

```bash
# 1. Clone the app repo
git clone https://github.com/mariamendieta/personal-finance-app.git
cd personal-finance-app

# 2. Clone your data repo into Production/
git clone https://github.com/YOUR_USER/YOUR_DATA_REPO.git Production

# 3. Run the cash flow pipeline
cd Production && python3 cashflow.py && cd ..

# 4. Start the app in production mode
DATA_MODE=production python3 -m uvicorn backend.app.main:app --port 8000 &
cd frontend && npm run dev -- -p 3001
```

### Production data structure

Your private data repo should have this structure inside `Production/`:

```
Production/
├── cashflow.py                 ← cash flow pipeline script
├── ActionItems.md              ← action items table
├── accounts.json               ← account definitions
├── transaction_notes.json      ← notes on individual transactions
├── CashFlow/
│   ├── 2025/                   ← annual CSV exports
│   │   ├── Checking and Savings/
│   │   └── Credit Cards/
│   ├── Jan26/                  ← monthly CSV exports
│   │   ├── Checking and Savings/
│   │   └── Credit Cards/
│   ├── Monthly/                ← generated monthly summaries
│   └── all_transactions.csv    ← generated master file
└── InvestmentPortfolio/
    └── {date}/                 ← dated snapshots
```

## Supported Account Formats

The app auto-detects CSV formats from these institutions:

| Institution | Account Types | Format |
|-------------|--------------|--------|
| Chase | Credit cards, Checking | Chase card/checking format |
| Capital One | Credit cards | Debit/Credit columns |
| Bank of America | Credit cards, Checking/Savings | BoA card/bank format |
| SoFi | Checking, Savings | SoFi format |
| Citi | Credit cards | Citi format |
| Barclays | Credit cards | Barclays format |

## Project Structure

```
personal-finance-app/
├── README.md
├── .gitignore
├── generate_demo_data.py       ← generates Demo/ with fake data
├── backend/
│   └── app/
│       ├── main.py             ← FastAPI app
│       ├── routers/            ← API endpoints
│       └── services/           ← business logic
├── frontend/
│   └── src/
│       ├── app/                ← Next.js pages
│       ├── components/         ← React components
│       └── lib/                ← API client & utilities
├── Demo/                       ← demo data + scripts
│   ├── cashflow.py
│   ├── CashFlow/
│   └── InvestmentPortfolio/
├── Production/                 ← .gitignored (private data repo)
└── BrandGuidelines/
```

## Monthly Update Workflow

1. Download CSV exports from all bank/credit card accounts
2. Upload them via the app's upload page, or place them in `Production/CashFlow/{MonthYear}/`
3. Run the pipeline: `cd Production && python3 cashflow.py`
4. Restart the backend to pick up new data
5. Review the dashboard for any unclassified transactions

## Requirements

- Python 3.9+
- Node.js 18+
- npm

```bash
# Python dependencies
pip3 install fastapi uvicorn pandas openpyxl

# Frontend dependencies
cd frontend && npm install
```
