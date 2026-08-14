from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.database import get_db
from app.ai_agent.chatbot import stream_chat_response
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    return StreamingResponse(
        stream_chat_response(payload.session_id, payload.message, db),
        media_type="text/event-stream",
    )
