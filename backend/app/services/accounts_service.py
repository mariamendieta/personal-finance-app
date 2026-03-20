"""Accounts service — manages the list of known accounts with hide/show support."""

import json
from ..config import DATA_DIR, IS_DEMO

ACCOUNTS_FILE = DATA_DIR / "accounts.json"

PRODUCTION_ACCOUNTS = {
    "credit_cards": [
        {"label": "Aeroplan (Chase)", "filePrefix": "Aeroplan", "hidden": False},
        {"label": "AmazonPrime (Chase)", "filePrefix": "AmazonPrime", "hidden": False},
        {"label": "United (Chase)", "filePrefix": "United", "hidden": False},
        {"label": "VentureX (Capital One)", "filePrefix": "VentureX", "hidden": False},
        {"label": "VentureOne (Capital One)", "filePrefix": "VentureOne", "hidden": False},
        {"label": "Alaska (BofA)", "filePrefix": "Alaska", "hidden": False},
    ],
    "bank_accounts": [
        {"label": "SoFi Joint Checking", "filePrefix": "SOFI-JointChecking", "hidden": False},
        {"label": "SoFi Joint Savings", "filePrefix": "SOFI-JointSavings", "hidden": False},
        {"label": "BoA Checking", "filePrefix": "BoA-Checking", "hidden": False},
        {"label": "BoA Savings", "filePrefix": "BoA-Savings", "hidden": False},
        {"label": "Chase Checking", "filePrefix": "Chase-Checking", "hidden": False},
    ],
}

DEMO_ACCOUNTS = {
    "credit_cards": [
        {"label": "Rewards Visa", "filePrefix": "RewardsVisa", "hidden": False},
        {"label": "Travel Card", "filePrefix": "TravelCard", "hidden": False},
        {"label": "Cash Back Card", "filePrefix": "CashBackCard", "hidden": False},
    ],
    "bank_accounts": [
        {"label": "Joint Checking", "filePrefix": "JointChecking", "hidden": False},
        {"label": "Joint Savings", "filePrefix": "JointSavings", "hidden": False},
        {"label": "Emergency Fund", "filePrefix": "EmergencyFund", "hidden": False},
    ],
}

DEFAULT_ACCOUNTS = DEMO_ACCOUNTS if IS_DEMO else PRODUCTION_ACCOUNTS


def _load() -> dict:
    if not ACCOUNTS_FILE.exists():
        _save(DEFAULT_ACCOUNTS)
        return DEFAULT_ACCOUNTS.copy()
    return json.loads(ACCOUNTS_FILE.read_text())


def _save(data: dict):
    ACCOUNTS_FILE.write_text(json.dumps(data, indent=2) + "\n")


def get_accounts() -> dict:
    """Return the full accounts dict, creating default if file doesn't exist."""
    return _load()


def add_account(account_type: str, label: str, file_prefix: str) -> dict:
    """Add a new account to the list. account_type is 'credit_cards' or 'bank_accounts'."""
    data = _load()
    if account_type not in data:
        data[account_type] = []

    # Avoid duplicates by filePrefix
    existing_prefixes = {a["filePrefix"] for a in data[account_type]}
    if file_prefix not in existing_prefixes:
        data[account_type].append({
            "label": label,
            "filePrefix": file_prefix,
            "hidden": False,
        })
        _save(data)

    return data


def toggle_account(account_type: str, file_prefix: str, hidden: bool) -> dict:
    """Set the hidden flag for an account identified by type and filePrefix."""
    data = _load()
    if account_type in data:
        for account in data[account_type]:
            if account["filePrefix"] == file_prefix:
                account["hidden"] = hidden
                break
        _save(data)
    return data
