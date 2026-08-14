from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.models.campaign import Campaign
from app.email_agent.drafter import draft_email
from app.email_agent.sender import send_email

router = APIRouter()


class EmailDraftRequest(BaseModel):
    lead_id: UUID
    campaign_context: str | None = None


class EmailSendRequest(BaseModel):
    lead_id: UUID
    subject: str
    body: str


@router.post("/draft")
async def draft(payload: EmailDraftRequest, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    result = await draft_email(lead, payload.campaign_context)
    return result


@router.post("/send")
async def send(payload: EmailSendRequest, db: AsyncSession = Depends(get_db)):
    lead = await db.get(Lead, payload.lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    if not lead.email:
        raise HTTPException(400, "Lead has no email address")
    result = await send_email(lead.email, payload.subject, payload.body)
    # Update lead status
    lead.status = "contacted"
    await db.commit()
    return result


# ── Email Traffic & Records ────────────────────────────────────────────────────


@router.get("/logs")
async def email_logs(
    status: str | None = None,
    search: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List email traffic records (logs) with lead + campaign info, paginated."""
    query = (
        select(EmailLog, Lead.name.label("lead_name"), Campaign.name.label("campaign_name"))
        .outerjoin(Lead, Lead.id == EmailLog.lead_id)
        .outerjoin(Campaign, Campaign.id == EmailLog.campaign_id)
    )

    if status:
        query = query.where(EmailLog.status == status)
    if search:
        query = query.where(
            func.lower(EmailLog.recipient_email).like(f"%{search.lower()}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(
        query.order_by(EmailLog.sent_at.desc().nulls_last(), EmailLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    rows = result.all()

    data = []
    for row in rows:
        log, lead_name, campaign_name = row
        data.append({
            "id": str(log.id),
            "lead_id": str(log.lead_id) if log.lead_id else None,
            "lead_name": lead_name,
            "campaign_id": str(log.campaign_id) if log.campaign_id else None,
            "campaign_name": campaign_name,
            "recipient_email": log.recipient_email,
            "recipient_name": log.recipient_name,
            "subject": log.subject,
            "status": log.status,
            "error_message": log.error_message,
            "opened_at": log.opened_at.isoformat() if log.opened_at else None,
            "opened_count": log.opened_count,
            "clicked_at": log.clicked_at.isoformat() if log.clicked_at else None,
            "clicked_count": log.clicked_count,
            "replied_at": log.replied_at.isoformat() if log.replied_at else None,
            "is_follow_up": log.is_follow_up,
            "follow_up_number": log.follow_up_number,
            "sent_at": log.sent_at.isoformat() if log.sent_at else None,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {"total": total, "page": page, "page_size": page_size, "data": data}


class ReplyLogRequest(BaseModel):
    reply_content: str | None = None


@router.post("/logs/{email_log_id}/reply")
async def mark_email_replied(
    email_log_id: UUID,
    payload: ReplyLogRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Manually mark an email log as replied (for testing when no IMAP monitor
    is configured). Optionally accepts reply content.
    """
    email_log = await db.get(EmailLog, email_log_id)
    if not email_log:
        raise HTTPException(404, "Email log not found")

    email_log.replied_at = email_log.replied_at or datetime.now(timezone.utc)
    if payload and payload.reply_content:
        email_log.extra_data = email_log.extra_data or {}
        email_log.extra_data["reply_content"] = payload.reply_content

    # Also update the associated lead's status
    if email_log.lead_id:
        lead = await db.get(Lead, email_log.lead_id)
        if lead and lead.status != "enrolled":
            lead.status = "replied"

    await db.commit()
    await db.refresh(email_log)

    return {
        "email_log_id": str(email_log.id),
        "replied_at": email_log.replied_at.isoformat() if email_log.replied_at else None,
    }
