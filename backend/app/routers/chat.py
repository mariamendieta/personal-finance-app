"""Chat API endpoint — answers financial questions from local data."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    response: str


@router.post("/", response_model=ChatResponse)
def chat(request: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    response = chat_service.get_chat_response(messages)
    return ChatResponse(response=response)
