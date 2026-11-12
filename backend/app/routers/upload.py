"""File upload and pipeline execution endpoints."""

import asyncio
import importlib.util
import re
import types
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from ..config import CASHFLOW_ROOT, DATA_DIR, PORTFOLIO_ROOT
from ..services import cashflow_service, portfolio_service

router = APIRouter(prefix="/api/upload", tags=["upload"])

SAFE_FILENAME = re.compile(r"^[\w\-. ()'&,]+\.csv$", re.I)

# Two month-folder naming conventions coexist in the data: the current
# "YYYY-MM_Mon" convention, and an older "MonYY" short form.
MONTH_FOLDER_LONG = re.compile(r"^(\d{4})-(\d{2})_[A-Za-z]+$")
MONTH_FOLDER_SHORT = re.compile(r"^([A-Za-z]{3})(\d{2})$")
MONTH_ABBR_TO_NUM = {abbr: i for i, abbr in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1
)}


class DeleteCashflowFileRequest(BaseModel):
    month_folder: str
    subfolder: str
    filename: str


@router.post("/cashflow")
async def upload_cashflow(
    month_folder: str = Form(...),
    files: list[UploadFile] = File(...),
    subfolder: str = Form("Credit Cards"),
    run_pipeline: bool = Form(True),
    run_report: bool = Form(True),
):
    if subfolder not in ("Credit Cards", "Checking and Savings"):
        return {"error": "Invalid subfolder"}

    dest = CASHFLOW_ROOT / month_folder / subfolder
    dest.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        if not f.filename or not SAFE_FILENAME.match(f.filename):
            continue
        filepath = dest / f.filename
        content = await f.read()
        filepath.write_bytes(content)
        saved.append(f.filename)

    results = []
    if run_pipeline:
        proc = await asyncio.create_subprocess_exec(
            "python3", str(DATA_DIR / "cashflow.py"),
            cwd=str(DATA_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        results.append({
            "script": "cashflow.py",
            "success": proc.returncode == 0,
            "output": (stdout or stderr).decode()[-500:],
        })
        cashflow_service.invalidate_cache()

    if run_report:
        report_script = DATA_DIR / "generate_report.py"
        if report_script.exists():
            proc = await asyncio.create_subprocess_exec(
                "python3", str(report_script),
                cwd=str(DATA_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            results.append({
                "script": "generate_report.py",
                "success": proc.returncode == 0,
                "output": (stdout or stderr).decode()[-500:],
            })

    return {"saved": saved, "saved_count": len(saved), "pipeline_results": results}


def _has_any_csv(d: Path) -> bool:
    return any(f.name != ".placeholder.csv" for f in d.rglob("*.csv"))


def _parsed_month_folders() -> list[tuple[int, int, str]]:
    """Every real (non-empty) month folder, as (year, month, folder_name)."""
    if not CASHFLOW_ROOT.is_dir():
        return []

    entries: list[tuple[int, int, str]] = []
    for d in CASHFLOW_ROOT.iterdir():
        if not d.is_dir():
            continue
        m = MONTH_FOLDER_LONG.match(d.name)
        if m:
            if _has_any_csv(d):
                entries.append((int(m.group(1)), int(m.group(2)), d.name))
            continue
        m = MONTH_FOLDER_SHORT.match(d.name)
        if m:
            month = MONTH_ABBR_TO_NUM.get(m.group(1).capitalize())
            if month and _has_any_csv(d):
                entries.append((2000 + int(m.group(2)), month, d.name))
    return entries


@router.get("/cashflow/months")
async def list_cashflow_months():
    entries = sorted(_parsed_month_folders(), key=lambda e: (e[0], e[1]), reverse=True)
    return [name for _, _, name in entries]


def _load_cashflow_module():
    module_path = DATA_DIR / "cashflow.py"
    spec = importlib.util.spec_from_file_location("cashflow", str(module_path))
    mod = types.ModuleType("cashflow")
    mod.__file__ = str(module_path)
    spec.loader.exec_module(mod)
    return mod


@router.get("/cashflow/coverage")
async def cashflow_coverage():
    """For every real month folder and every account cashflow.py recognizes,
    whether at least one file for that account exists in that month — lets
    the UI show gaps across the whole history, not just one month at a time.
    """
    entries = sorted(_parsed_month_folders(), key=lambda e: (e[0], e[1]))
    months = [name for _, _, name in entries]

    cf = _load_cashflow_module()

    # account_name -> subfolder it was found in ("Credit Cards" / "Checking and Savings")
    account_subfolder: dict[str, str] = {}
    # account_name -> set of month folders that have at least one file for it
    coverage: dict[str, set[str]] = {}

    for month in months:
        for subfolder in ("Credit Cards", "Checking and Savings"):
            sub_path = CASHFLOW_ROOT / month / subfolder
            if not sub_path.is_dir():
                continue
            for f in sub_path.iterdir():
                if not f.is_file() or f.name.startswith("."):
                    continue
                parser, account_name = cf.detect_parser(f)
                if parser is None:
                    continue
                account_subfolder.setdefault(account_name, subfolder)
                coverage.setdefault(account_name, set()).add(month)

    accounts = sorted(
        account_subfolder.keys(),
        key=lambda a: (account_subfolder[a] != "Credit Cards", a.lower()),
    )

    return {
        "months": months,
        "accounts": [{"name": a, "subfolder": account_subfolder[a]} for a in accounts],
        "coverage": {a: sorted(coverage[a]) for a in accounts},
    }


@router.get("/cashflow/list")
async def list_cashflow_files(month_folder: str):
    result: dict[str, list[str]] = {}
    for subfolder in ("Credit Cards", "Checking and Savings"):
        dest = CASHFLOW_ROOT / month_folder / subfolder
        if not dest.is_dir():
            result[subfolder] = []
            continue
        result[subfolder] = sorted(
            f.name for f in dest.iterdir()
            if f.is_file() and f.name != ".placeholder.csv"
        )
    return result


@router.delete("/cashflow/file")
async def delete_cashflow_file(request: DeleteCashflowFileRequest):
    if request.subfolder not in ("Credit Cards", "Checking and Savings"):
        return {"error": "Invalid subfolder"}
    if not request.filename or not SAFE_FILENAME.match(request.filename):
        return {"error": "Invalid filename"}

    dest_dir = (CASHFLOW_ROOT / request.month_folder / request.subfolder).resolve()
    filepath = (dest_dir / request.filename).resolve()
    if dest_dir not in filepath.parents or not filepath.is_file():
        return {"error": "File not found"}

    filepath.unlink()
    return {"deleted": request.filename}


@router.post("/portfolio")
async def upload_portfolio(
    snapshot_date: str = Form(...),
    files: list[UploadFile] = File(...),
    run_analysis: bool = Form(True),
):
    dest = PORTFOLIO_ROOT / snapshot_date / "Investments&Balances"
    dest.mkdir(parents=True, exist_ok=True)

    saved = []
    for f in files:
        if not f.filename or not SAFE_FILENAME.match(f.filename):
            continue
        filepath = dest / f.filename
        content = await f.read()
        filepath.write_bytes(content)
        saved.append(f.filename)

    results = []
    if run_analysis:
        proc = await asyncio.create_subprocess_exec(
            "python3", str(DATA_DIR / "portfolio.py"),
            cwd=str(DATA_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        results.append({
            "script": "portfolio.py",
            "success": proc.returncode == 0,
            "output": (stdout or stderr).decode()[-500:],
        })
        portfolio_service.invalidate_cache()

    return {"saved": saved, "saved_count": len(saved), "pipeline_results": results}
