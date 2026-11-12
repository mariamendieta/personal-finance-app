"""Coverage service — tracks which accounts are marked as not currently used,
so the Coverage tab doesn't keep flagging them as gaps."""

import json
from ..config import DATA_DIR

IGNORED_FILE = DATA_DIR / "coverage_ignored.json"


def _load() -> set[str]:
    if not IGNORED_FILE.exists():
        return set()
    return set(json.loads(IGNORED_FILE.read_text()).get("ignored", []))


def _save(ignored: set[str]):
    IGNORED_FILE.write_text(json.dumps({"ignored": sorted(ignored)}, indent=2) + "\n")


def get_ignored() -> set[str]:
    return _load()


def set_ignored(account_name: str, ignored: bool) -> set[str]:
    data = _load()
    if ignored:
        data.add(account_name)
    else:
        data.discard(account_name)
    _save(data)
    return data
