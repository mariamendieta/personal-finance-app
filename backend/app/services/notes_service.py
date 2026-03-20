"""Transaction notes service — manage per-transaction notes stored in JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..config import DATA_DIR

NOTES_FILE: Path = DATA_DIR / "transaction_notes.json"


def _read_notes() -> dict:
    if NOTES_FILE.exists():
        return json.loads(NOTES_FILE.read_text())
    return {}


def _write_notes(notes: dict) -> None:
    NOTES_FILE.write_text(json.dumps(notes, indent=2) + "\n")


def make_key(date: str, description: str, amount: float, account: str) -> str:
    return f"{date}|{description}|{round(amount, 2)}|{account}"


def get_all_notes() -> dict:
    return _read_notes()


def get_note(key: str) -> Optional[str]:
    return _read_notes().get(key)


def set_note(date: str, description: str, amount: float, account: str, note: str) -> dict:
    notes = _read_notes()
    key = make_key(date, description, amount, account)
    notes[key] = note
    _write_notes(notes)
    return notes


def delete_note(date: str, description: str, amount: float, account: str) -> dict:
    notes = _read_notes()
    key = make_key(date, description, amount, account)
    notes.pop(key, None)
    _write_notes(notes)
    return notes
