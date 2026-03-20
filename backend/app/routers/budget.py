"""Budget API endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services import budget_service

router = APIRouter(prefix="/api/budget", tags=["budget"])


class BudgetPayload(BaseModel):
    budgets: dict[str, float]


@router.get("/")
def get_budgets():
    return budget_service.get_budgets()


@router.put("/")
def set_budgets(payload: BudgetPayload):
    return budget_service.set_budgets(payload.budgets)


@router.get("/vs-actual")
def budget_vs_actual(months: int = Query(1, ge=1, le=60)):
    return budget_service.get_budget_vs_actual(months)


@router.get("/categories")
def available_categories():
    return budget_service.get_available_categories()
