"""
Chatbot routes — streaming AI admissions assistant for President University.

Endpoints:
  POST /chat              — Send a message (SSE streaming response)
  GET  /history/{sid}     — Get conversation history for a session
  DELETE /history/{sid}   — Clear conversation history
  GET  /sessions          — List active session IDs (admin only)
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.ai_agent.chatbot import (
    stream_chat_response,
    get_history,
    clear_history,
    list_sessions,
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    session_id: str
    message: str


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/chat")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Stream a chat response from the AI assistant.
    Uses Server-Sent Events (SSE) format.
    Maintains conversation history per session_id.
    """
    return StreamingResponse(
        stream_chat_response(payload.session_id, payload.message, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for SSE
        },
    )


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str):
    """
    Return the conversation history for a session.
    History is stored in-memory and resets on server restart.
    """
    history = get_history(session_id)
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": history,
    }


@router.delete("/history/{session_id}")
async def clear_chat_history(session_id: str):
    """
    Clear the conversation history for a session.
    Call this when the user starts a new conversation.
    """
    clear_history(session_id)
    return {"session_id": session_id, "cleared": True}


@router.get("/sessions")
async def list_chat_sessions(_: User = Depends(require_admin)):
    """
    List all active session IDs (admin only).
    """
    sessions = list_sessions()
    return {
        "total_sessions": len(sessions),
        "sessions": sessions,
    }
