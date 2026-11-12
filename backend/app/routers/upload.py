"""File upload and pipeline execution endpoints."""

import asyncio
import re
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from ..config import CASHFLOW_ROOT, DATA_DIR, PORTFOLIO_ROOT
from ..services import cashflow_service, portfolio_service

router = APIRouter(prefix="/api/upload", tags=["upload"])

SAFE_FILENAME = re.compile(r"^[\w\-. ()'&,]+\.csv$", re.I)


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
