"""File upload and pipeline execution endpoints."""

import asyncio
import re
from pathlib import Path

from fastapi import APIRouter, File, Form, UploadFile

from ..config import CASHFLOW_ROOT, DATA_DIR, PORTFOLIO_ROOT
from ..services import cashflow_service, portfolio_service

router = APIRouter(prefix="/api/upload", tags=["upload"])

SAFE_FILENAME = re.compile(r"^[\w\-. ()'&,]+\.csv$", re.I)


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
