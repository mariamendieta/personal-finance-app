"""Transaction notes API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services import notes_service

router = APIRouter(prefix="/api/notes", tags=["notes"])


class NoteRequest(BaseModel):
    date: str
    description: str
    amount: float
    account: str
    note: str


class NoteDeleteRequest(BaseModel):
    date: str
    description: str
    amount: float
    account: str


@router.get("/")
def get_all_notes():
    return notes_service.get_all_notes()


@router.put("/")
def set_note(req: NoteRequest):
    return notes_service.set_note(req.date, req.description, req.amount, req.account, req.note)


@router.delete("/")
def delete_note(req: NoteDeleteRequest):
    return notes_service.delete_note(req.date, req.description, req.amount, req.account)
