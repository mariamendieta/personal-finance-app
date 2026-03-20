"""Cash flow API endpoints."""

from fastapi import APIRouter, Query

from ..services import cashflow_service

router = APIRouter(prefix="/api/cashflow", tags=["cashflow"])


@router.get("/summary")
def summary(months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_summary(months)


@router.get("/monthly-expenses")
def monthly_expenses(months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_monthly_expenses(months)


@router.get("/monthly-income")
def monthly_income(months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_monthly_income(months)


@router.get("/net-income")
def net_income(months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_net_income(months)


@router.get("/spending-by-category")
def spending_by_category(months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_spending_by_category(months)


@router.get("/subcategories")
def subcategories(category: str = Query(...), months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_subcategories(category, months)


@router.get("/subcategory-vendors")
def subcategory_vendors(category: str = Query(...), subcategory: str = Query(...), months: int = Query(12, ge=1, le=60)):
    return cashflow_service.get_subcategory_vendors(category, subcategory, months)


@router.get("/top-vendors")
def top_vendors(months: int = Query(12, ge=1, le=60), limit: int = Query(10, ge=1, le=50)):
    return cashflow_service.get_top_vendors(months, limit)
