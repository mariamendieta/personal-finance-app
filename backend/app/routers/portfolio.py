"""Portfolio API endpoints."""

from fastapi import APIRouter, Query

from ..services import portfolio_service

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("/snapshots")
def snapshots():
    return portfolio_service.get_snapshots()


@router.get("/summary")
def summary(snapshot: str = Query(...)):
    return portfolio_service.get_summary(snapshot)


@router.get("/asset-allocation")
def asset_allocation(snapshot: str = Query(...)):
    return portfolio_service.get_asset_allocation(snapshot)


@router.get("/by-account")
def by_account(snapshot: str = Query(...)):
    return portfolio_service.get_by_account(snapshot)


@router.get("/retirement-vs-taxable")
def retirement_vs_taxable(snapshot: str = Query(...)):
    return portfolio_service.get_retirement_vs_taxable(snapshot)


@router.get("/compare")
def compare(current: str = Query(...), previous: str = Query(...)):
    return portfolio_service.get_comparison(current, previous)
