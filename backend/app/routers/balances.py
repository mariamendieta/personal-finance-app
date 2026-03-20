"""Account balances API endpoints."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from ..services import balances_service

router = APIRouter(prefix="/api/balances", tags=["balances"])


class SaveBalancesRequest(BaseModel):
    date: str
    balances: dict[str, float]


@router.get("/")
def get_balances(date: str = Query(...)):
    return balances_service.get_balances(date)


@router.get("/all")
def get_all_balances():
    return balances_service.get_all_balances()


@router.put("/")
def save_balances(request: SaveBalancesRequest):
    return balances_service.save_balances(request.date, request.balances)
