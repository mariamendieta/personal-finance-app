"""Action items API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services import action_items_service

router = APIRouter(prefix="/api/action-items", tags=["action-items"])


class ActionItem(BaseModel):
    task: str
    assignee: str
    category: str
    date_created: str
    status: str
    date_completed: str


class AddItemRequest(BaseModel):
    task: str
    assignee: str
    category: str = "Other"
    date_created: str


class UpdateStatusRequest(BaseModel):
    task: str
    status: str
    date_completed: str = ""


class DeleteItemRequest(BaseModel):
    task: str


@router.get("/", response_model=list[ActionItem])
def get_items():
    return action_items_service.get_action_items()


@router.post("/", response_model=list[ActionItem])
def add_item(request: AddItemRequest):
    return action_items_service.add_action_item(
        request.task, request.assignee, request.category, request.date_created,
    )


@router.put("/status", response_model=list[ActionItem])
def update_status(request: UpdateStatusRequest):
    return action_items_service.update_action_item_status(
        request.task, request.status, request.date_completed,
    )


@router.delete("/", response_model=list[ActionItem])
def delete_item(request: DeleteItemRequest):
    return action_items_service.delete_action_item(request.task)
