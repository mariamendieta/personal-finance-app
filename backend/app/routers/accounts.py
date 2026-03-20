"""Accounts router — CRUD for the account list with hide/show support."""

from fastapi import APIRouter
from pydantic import BaseModel
from ..services import accounts_service

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


class AddAccountRequest(BaseModel):
    account_type: str
    label: str
    file_prefix: str


class ToggleAccountRequest(BaseModel):
    account_type: str
    file_prefix: str
    hidden: bool


@router.get("/")
def get_accounts():
    return accounts_service.get_accounts()


@router.post("/")
def add_account(req: AddAccountRequest):
    return accounts_service.add_account(req.account_type, req.label, req.file_prefix)


@router.put("/toggle")
def toggle_account(req: ToggleAccountRequest):
    return accounts_service.toggle_account(req.account_type, req.file_prefix, req.hidden)
