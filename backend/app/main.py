"""FastAPI application — Woffieta Finances API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import BRAND, BRAND_PALETTE, DATA_MODE, FAMILY_NAME, IS_DEMO
from .routers import accounts, action_items, balances, budget, cashflow, chat, notes, portfolio, upload

app = FastAPI(title="Woffieta Finances API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(balances.router)
app.include_router(budget.router)
app.include_router(cashflow.router)
app.include_router(portfolio.router)
app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(action_items.router)
app.include_router(notes.router)


@app.get("/api/config")
def get_config():
    return {
        "family_name": FAMILY_NAME,
        "is_demo": IS_DEMO,
        "data_mode": DATA_MODE,
        "brand": BRAND,
        "brand_palette": BRAND_PALETTE,
    }
