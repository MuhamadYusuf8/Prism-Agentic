"""
Email Tracking & Conversation Monitoring routes.

Endpoints:
    GET  /api/email/monitoring/overview                → aggregate tracking stats
    GET  /api/email/monitoring/conversations           → list conversations
    GET  /api/email/monitoring/conversations/{key}     → full thread (lead UUID or email)
    POST /api/email/monitoring/sync-inbox              → ingest replies from IMAP mailbox
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.monitoring import get_overview, list_conversations, get_conversation

router = APIRouter()


@router.get("/overview")
async def email_monitoring_overview(db: AsyncSession = Depends(get_db)):
    """Aggregate email tracking stats (sent / opened / clicked / replied / bounced / failed)."""
    return await get_overview(db)


@router.get("/conversations")
async def email_conversations(
    search: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List one summary row per conversation (student ↔ us)."""
    return await list_conversations(
        db,
        search=search,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get("/conversations/{key}")
async def email_conversation_detail(
    key: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Full conversation thread for a student.

    `key` is either a lead UUID (e.g. /conversations/<lead-uuid>) or a
    recipient email address (e.g. /conversations/student%40gmail.com).
    """
    thread = await get_conversation(db, key)
    return thread


@router.post("/sync-inbox")
async def sync_email_inbox(db: AsyncSession = Depends(get_db)):
    """Fetch unread replies from the configured IMAP mailbox (e.g. mit@president.ac.id)."""
    from app.services.mailbox_monitor import sync_inbox

    result = await sync_inbox(db)
    if result.get("errors"):
        result["errors"] = result["errors"][:20]
    return result
