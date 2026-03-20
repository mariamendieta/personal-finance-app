"""Action items service — reads/writes ActionItems.md."""

from ..config import DATA_DIR

ACTION_ITEMS_FILE = DATA_DIR / "ActionItems.md"

STATUS_ORDER = {"In Progress": 0, "Open": 1, "Done": 2}
CATEGORIES = ["Cash Flow", "Investment", "Other"]


def _parse_table(content: str) -> list[dict]:
    """Parse markdown table into list of dicts."""
    lines = content.strip().split("\n")
    items = []
    for line in lines:
        line = line.strip()
        if not line.startswith("|") or line.startswith("| Task") or line.startswith("|---"):
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 6:
            items.append({
                "task": cols[0],
                "assignee": cols[1],
                "category": cols[2],
                "date_created": cols[3],
                "status": cols[4],
                "date_completed": cols[5],
            })
    return items


def _sort_items(items: list[dict]) -> list[dict]:
    """Sort by status: In Progress, Open, Done."""
    return sorted(items, key=lambda x: STATUS_ORDER.get(x["status"], 1))


def _write_table(items: list[dict]) -> str:
    """Convert list of dicts back to markdown table."""
    lines = [
        "# Action Items",
        "",
        "| Task | Assignee | Category | Date Created | Status | Date Completed |",
        "|------|----------|----------|-------------|--------|----------------|",
    ]
    for item in items:
        lines.append(
            f"| {item['task']} | {item['assignee']} | {item['category']} | {item['date_created']} | {item['status']} | {item['date_completed']} |"
        )
    return "\n".join(lines) + "\n"


def get_action_items() -> list[dict]:
    if not ACTION_ITEMS_FILE.exists():
        return []
    content = ACTION_ITEMS_FILE.read_text()
    return _parse_table(content)


def save_action_items(items: list[dict]):
    sorted_items = _sort_items(items)
    ACTION_ITEMS_FILE.write_text(_write_table(sorted_items))
    return sorted_items


def add_action_item(task: str, assignee: str, category: str, date_created: str) -> list[dict]:
    items = get_action_items()
    items.append({
        "task": task,
        "assignee": assignee,
        "category": category if category in CATEGORIES else "Other",
        "date_created": date_created,
        "status": "Open",
        "date_completed": "",
    })
    return save_action_items(items)


def update_action_item_status(task: str, status: str, date_completed: str = "") -> list[dict]:
    items = get_action_items()
    for item in items:
        if item["task"] == task:
            item["status"] = status
            item["date_completed"] = date_completed
            break
    return save_action_items(items)


def update_action_item(old_task: str, task: str, assignee: str, category: str) -> list[dict]:
    items = get_action_items()
    for item in items:
        if item["task"] == old_task:
            item["task"] = task
            item["assignee"] = assignee
            item["category"] = category if category in CATEGORIES else "Other"
            break
    return save_action_items(items)


def delete_action_item(task: str) -> list[dict]:
    items = get_action_items()
    items = [i for i in items if i["task"] != task]
    return save_action_items(items)
