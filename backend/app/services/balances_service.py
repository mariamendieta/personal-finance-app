"""Account balances service — stores current balances by account and date."""

import json
from ..config import DATA_DIR

BALANCES_FILE = DATA_DIR / "balances.json"


def _load() -> dict:
    if not BALANCES_FILE.exists():
        return {}
    return json.loads(BALANCES_FILE.read_text())


def _save(data: dict):
    BALANCES_FILE.write_text(json.dumps(data, indent=2) + "\n")


def get_balances(date: str) -> dict:
    """Get balances for a specific date. Returns {account: balance}."""
    data = _load()
    return data.get(date, {})


def get_all_balances() -> dict:
    """Get all balances keyed by date."""
    return _load()


def save_balances(date: str, balances: dict[str, float]) -> dict:
    """Save balances for a date. Merges with existing."""
    data = _load()
    if date not in data:
        data[date] = {}
    data[date].update(balances)
    _save(data)
    return data[date]
