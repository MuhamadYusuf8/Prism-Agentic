"""
Email Tracking & Conversation Monitoring routes.

Endpoints:
    GET  /api/email/monitoring/overview                → aggregate tracking stats
    GET  /api/email/monitoring/conversations           → list conversations
    GET  /api/email/monitoring/conversations/{key}     → full thread (lead UUID or email)
    POST /api/email/monitoring/sync-inbox              → ingest replies from IMAP mailbox
    POST /api/email/monitoring/process-reply           → manually process an incoming reply
    GET  /api/email/monitoring/replies                 → list all replies with filters
    POST /api/email/monitoring/trigger-follow-ups      → trigger background follow-ups
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.models.reply import Reply
from app.models.email_log import EmailLog
from app.services.monitoring import get_overview, list_conversations, get_conversation

router = APIRouter()


# ── Overview ──────────────────────────────────────────────────────────────────


@router.get("/overview")
async def email_monitoring_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Aggregate email tracking stats (sent / opened / clicked / replied / bounced / failed)."""
    return await get_overview(db)


# ── Conversations ─────────────────────────────────────────────────────────────


@router.get("/conversations")
async def email_conversations(
    search: str | None = None,
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
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
    _: User = Depends(get_current_user),
):
    """
    Full conversation thread for a student.

    `key` is either a lead UUID (e.g. /conversations/<lead-uuid>) or a
    recipient email address (e.g. /conversations/student%40gmail.com).
    """
    thread = await get_conversation(db, key)
    return thread


# ── IMAP Inbox Sync ───────────────────────────────────────────────────────────


@router.post("/sync-inbox")
async def sync_email_inbox(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Fetch unread replies from the configured IMAP mailbox (e.g. mit@president.ac.id)."""
    from app.services.mailbox_monitor import sync_inbox

    result = await sync_inbox(db)
    if result.get("errors"):
        result["errors"] = result["errors"][:20]
    return result


# ── Manual Reply Processing ───────────────────────────────────────────────────


class ProcessReplyPayload(BaseModel):
    from_email: str
    subject: str | None = None
    body: str
    body_text: str | None = None


@router.post("/process-reply")
async def process_incoming_reply(
    payload: ProcessReplyPayload,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Manually process an incoming email reply.
    Classifies intent, updates lead status, and sends auto-response if configured.
    Useful for testing the reply pipeline without a real IMAP inbox.
    """
    from app.services.reply_monitor import process_reply

    result = await process_reply(
        from_email=payload.from_email,
        subject=payload.subject,
        body=payload.body,
        body_text=payload.body_text,
        db=db,
    )
    return result


# ── Replies List ──────────────────────────────────────────────────────────────


@router.get("/replies")
async def list_all_replies(
    intent: str | None = None,
    sentiment: str | None = None,
    auto_responded: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    List all incoming replies across all campaigns.
    Can be filtered by intent, sentiment, or whether auto-response was sent.
    """
    query = select(Reply)
    if intent:
        query = query.where(Reply.intent == intent)
    if sentiment:
        query = query.where(Reply.sentiment == sentiment)
    if auto_responded is not None:
        query = query.where(Reply.auto_response_sent == auto_responded)

    total = await db.scalar(
        select(func.count()).select_from(
            select(Reply).subquery()
        )
    ) or 0

    result = await db.execute(
        query.order_by(Reply.received_at.desc().nulls_last())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    replies = result.scalars().all()

    # Intent distribution for this filter
    by_intent = await db.execute(
        select(Reply.intent, func.count(Reply.id)).group_by(Reply.intent)
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "intent_distribution": {row[0]: row[1] for row in by_intent},
        "data": [
            {
                "id": str(r.id),
                "from_email": r.from_email,
                "subject": r.subject,
                "body_text": r.body_text,
                "intent": r.intent,
                "sentiment": r.sentiment,
                "confidence": r.confidence,
                "auto_response_sent": r.auto_response_sent,
                "auto_response_at": r.auto_response_at.isoformat() if r.auto_response_at else None,
                "received_at": r.received_at.isoformat() if r.received_at else None,
                "campaign_id": str(r.campaign_id) if r.campaign_id else None,
                "lead_id": str(r.lead_id) if r.lead_id else None,
            }
            for r in replies
        ],
    }


# ── Trigger Follow-ups ────────────────────────────────────────────────────────


class TriggerFollowUpsPayload(BaseModel):
    campaign_id: str | None = None  # None = trigger for ALL active campaigns


@router.post("/trigger-follow-ups")
async def trigger_follow_up_emails(
    payload: TriggerFollowUpsPayload | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Trigger background follow-up email dispatch.
    If campaign_id is provided, only that campaign's follow-ups are sent.
    Otherwise, all active campaigns with follow-up enabled are processed.
    """
    from app.models.campaign import Campaign
    from app.workers.email_tasks import dispatch_follow_ups

    if payload and payload.campaign_id:
        # Single campaign
        campaign = await db.get(Campaign, payload.campaign_id)
        if not campaign:
            raise HTTPException(404, "Campaign not found")
        follow_up_cfg = campaign.follow_up or {}
        if not follow_up_cfg.get("enabled"):
            raise HTTPException(400, "Follow-ups not enabled for this campaign")
        task = dispatch_follow_ups.delay(payload.campaign_id)
        return {
            "status": "queued",
            "task_id": task.id,
            "message": f"Follow-ups queued for campaign '{campaign.name}'",
        }
    else:
        # All active campaigns with follow-up enabled
        result = await db.execute(
            select(Campaign).where(Campaign.status == "active")
        )
        active_campaigns = result.scalars().all()

        queued = []
        skipped = []
        for campaign in active_campaigns:
            follow_up_cfg = campaign.follow_up or {}
            if follow_up_cfg.get("enabled"):
                task = dispatch_follow_ups.delay(str(campaign.id))
                queued.append({
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "task_id": task.id,
                })
            else:
                skipped.append(campaign.name)

        return {
            "status": "queued",
            "queued_count": len(queued),
            "skipped_count": len(skipped),
            "queued": queued,
            "skipped": skipped,
            "message": f"Follow-ups queued for {len(queued)} campaign(s)",
        }
