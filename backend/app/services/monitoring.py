"""
Email Tracking & Conversation Monitoring service.

Builds a real-time picture of outreach health:

  - Per-email status lifecycle:  pending → sent → opened → clicked → replied
                                (or bounced / failed)
  - Full conversation threads between the sender (us) and each student,
    merging outgoing `EmailLog` records with incoming `Reply` records
    (including auto-responses that were sent back).

Everything is derived from existing tables — no schema migration required.
"""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead
from app.models.email_log import EmailLog
from app.models.reply import Reply


# ── Helpers ───────────────────────────────────────────────────────────────────


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _rank(status: str) -> int:
    """Higher rank = more progressed in the engagement lifecycle."""
    return {
        "replied": 5,
        "clicked": 4,
        "opened": 3,
        "bounced": 2,
        "failed": 1,
        "sent": 0,
        "logged": 0,
        "delivered": 0,
        "pending": -1,
    }.get(status, 0)


def best_status(statuses: list[str]) -> str:
    """Pick the most meaningful status out of a set of statuses."""
    return max(statuses, key=_rank)


def derive_email_status(log: EmailLog) -> str:
    """Derive the effective engagement status of a single EmailLog."""
    if log.status == "bounced":
        return "bounced"
    if log.status == "failed":
        return "failed"
    if log.status == "pending":
        return "pending"
    if log.status == "logged":
        return "logged"
    if log.replied_at:
        return "replied"
    if log.clicked_at:
        return "clicked"
    if log.opened_at:
        return "opened"
    return log.status or "sent"


def serialize_email_log(log: EmailLog) -> dict:
    """Serialize an outgoing email record for the monitoring API."""
    return {
        "id": str(log.id),
        "type": "email",
        "direction": "outgoing",
        "from_email": settings.EMAIL_FROM or "admissions@president.ac.id",
        "to_email": log.recipient_email,
        "recipient_name": log.recipient_name,
        "subject": log.subject,
        "body": log.body,
        "status": derive_email_status(log),
        "opened_at": _iso(log.opened_at),
        "opened_count": log.opened_count or 0,
        "clicked_at": _iso(log.clicked_at),
        "clicked_count": log.clicked_count or 0,
        "replied_at": _iso(log.replied_at),
        "is_follow_up": log.is_follow_up,
        "follow_up_number": log.follow_up_number or 0,
        "error_message": log.error_message,
        "sent_at": _iso(log.sent_at) or _iso(log.created_at),
        "campaign_id": str(log.campaign_id) if log.campaign_id else None,
    }


def serialize_reply(reply: Reply) -> dict:
    """Serialize an incoming reply record for the monitoring API."""
    return {
        "id": str(reply.id),
        "type": "reply",
        "direction": "incoming",
        "from_email": reply.from_email,
        "subject": reply.subject,
        "body": reply.body,
        "body_text": reply.body_text,
        "intent": reply.intent,
        "confidence": reply.confidence,
        "sentiment": reply.sentiment,
        "auto_response_sent": reply.auto_response_sent,
        "auto_response_at": _iso(reply.auto_response_at),
        "auto_response_body": reply.auto_response_body,
        "received_at": _iso(reply.received_at),
    }


# ── Overview ──────────────────────────────────────────────────────────────────


async def get_overview(db: AsyncSession) -> dict:
    """Aggregate email tracking stats across all sends + replies."""
    sent = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.status.in_(["sent", "delivered"])
        )
    )
    opened = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.opened_at.isnot(None))
    )
    clicked = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.clicked_at.isnot(None))
    )
    replied = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.replied_at.isnot(None))
    )
    bounced = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.status == "bounced")
    )
    failed = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.status == "failed")
    )
    pending = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.status == "pending")
    )
    total_emails = await db.scalar(select(func.count(EmailLog.id)))

    # Distinct recipients (leads + raw addresses) that have any traffic
    conversations = await db.scalar(
        select(func.count()).select_from(
            select(EmailLog.lead_id, EmailLog.recipient_email)
            .distinct()
            .subquery()
        )
    )

    # Distinct leads that ever replied
    replying_leads = await db.scalar(
        select(func.count()).select_from(
            select(Reply.lead_id).where(Reply.lead_id.isnot(None)).distinct().subquery()
        )
    )

    sent = sent or 0
    opened = opened or 0
    clicked = clicked or 0
    replied = replied or 0

    base = max(sent, 1)
    return {
        "total_emails": total_emails or 0,
        "sent": sent,
        "opened": opened,
        "clicked": clicked,
        "replied": replied,
        "bounced": bounced or 0,
        "failed": failed or 0,
        "pending": pending or 0,
        "conversations": conversations or 0,
        "replying_leads": replying_leads or 0,
        "rates": {
            "open_rate": round(opened / base * 100, 2),
            "click_rate": round(clicked / base * 100, 2),
            "reply_rate": round(replied / base * 100, 2),
            "bounce_rate": round((bounced or 0) / base * 100, 2),
        },
        "sender_email": settings.EMAIL_FROM,
    }


# ── Conversation listing ──────────────────────────────────────────────────────


def _conversation_key(log: EmailLog | Reply) -> str:
    """A stable key identifying a conversation (lead id, or recipient email)."""
    if isinstance(log, Reply):
        lead_id = getattr(log, "lead_id", None)
        if lead_id:
            return str(lead_id)
        return (log.from_email or "").lower()
    if log.lead_id:
        return str(log.lead_id)
    return (log.recipient_email or "").lower()


async def list_conversations(
    db: AsyncSession,
    search: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """
    List one summary row per conversation (lead / recipient).

    A conversation groups all outgoing EmailLogs and incoming Replies for a
    single lead (or raw recipient address when no lead is linked yet).
    """
    # All records that define conversations
    logs = (await db.execute(select(EmailLog))).scalars().all()
    replies = (await db.execute(select(Reply))).scalars().all()

    # Lead id → Lead for names (only the ones we care about)
    lead_ids = set()
    for log in logs:
        if log.lead_id:
            lead_ids.add(log.lead_id)
    for reply in replies:
        if reply.lead_id:
            lead_ids.add(reply.lead_id)

    leads = {}
    if lead_ids:
        lead_rows = (await db.execute(select(Lead).where(Lead.id.in_(lead_ids)))).scalars().all()
        leads = {str(l.id): l for l in lead_rows}

    # Build grouped conversations
    grouped: dict[str, dict] = {}

    def ensure(key: str, recipient_email: str | None, lead_id: str | None):
        if key not in grouped:
            grouped[key] = {
                "key": key,
                "lead_id": lead_id,
                "recipient_email": recipient_email,
                "lead_name": None,
                "emails_sent": 0,
                "replies_count": 0,
                "opened": 0,
                "clicked": 0,
                "replied": 0,
                "bounced": 0,
                "failed": 0,
                "statuses": [],
                "last_activity_at": None,
                "last_subject": None,
                "last_message": None,
                "last_direction": None,
                "last_intent": None,
            }
        return grouped[key]

    for log in logs:
        key = _conversation_key(log)
        lead_id = str(log.lead_id) if log.lead_id else None
        conv = ensure(key, log.recipient_email, lead_id)
        if lead_id:
            lead = leads.get(lead_id)
            if lead:
                conv["lead_name"] = lead.name
        conv["emails_sent"] += 1
        st = derive_email_status(log)
        conv["statuses"].append(st)
        if log.opened_at:
            conv["opened"] += 1
        if log.clicked_at:
            conv["clicked"] += 1
        if log.replied_at:
            conv["replied"] += 1
        if log.status == "bounced":
            conv["bounced"] += 1
        if log.status == "failed":
            conv["failed"] += 1
        ts = log.sent_at or log.created_at
        if ts and (conv["last_activity_at"] is None or ts > conv["last_activity_at"]):
            conv["last_activity_at"] = ts
            conv["last_subject"] = log.subject
            conv["last_direction"] = "outgoing"
            conv["last_message"] = None

    for reply in replies:
        key = _conversation_key(reply)
        lead_id = str(reply.lead_id) if reply.lead_id else None
        conv = ensure(key, reply.from_email, lead_id)
        if lead_id:
            lead = leads.get(lead_id)
            if lead:
                conv["lead_name"] = lead.name
        conv["replies_count"] += 1
        conv["statuses"].append("replied")
        ts = reply.received_at
        if conv["last_activity_at"] is None or ts > conv["last_activity_at"]:
            conv["last_activity_at"] = ts
            conv["last_subject"] = reply.subject
            conv["last_direction"] = "incoming"
            conv["last_message"] = (reply.body_text or reply.body or "")[:500]
            conv["last_intent"] = reply.intent
        # Replied emails also count towards the replied metric
        conv["replied"] += 1

    rows = []
    for conv in grouped.values():
        conv["status"] = best_status(conv["statuses"])
        conv["last_activity_at"] = _iso(conv["last_activity_at"])
        # Lead name fallback: use recipient email local-part
        if not conv["lead_name"] and conv["recipient_email"]:
            conv["lead_name"] = conv["recipient_email"]
        rows.append(conv)

    # Filters
    if search:
        needle = search.lower()
        rows = [
            r for r in rows
            if needle in (r["lead_name"] or "").lower()
            or needle in (r["recipient_email"] or "").lower()
            or needle in (r["last_subject"] or "").lower()
        ]
    if status and status != "all":
        rows = [r for r in rows if r["status"] == status]

    # Sort: most recently active first
    def _ts(r):
        return r["last_activity_at"] or ""
    rows.sort(key=_ts, reverse=True)

    total = len(rows)
    start = (page - 1) * page_size
    paged = rows[start : start + page_size]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": paged,
    }


# ── Single conversation thread ────────────────────────────────────────────────


async def get_conversation(db: AsyncSession, key: str) -> dict:
    """
    Return the full message thread for a conversation.

    `key` may be a lead UUID or a recipient email address. Messages are merged
    (outgoing EmailLogs + incoming Replies + auto-responses) and ordered by
    timestamp so the thread reads naturally.
    """
    lead = None
    recipient_email = None

    # Try UUID → lead
    try:
        lead_uuid = UUID(key)
    except (ValueError, AttributeError):
        lead_uuid = None

    if lead_uuid:
        lead = await db.get(Lead, lead_uuid)

    if not lead:
        # Fall back to looking up a lead by email, else treat as raw address
        result = await db.execute(
            select(Lead).where(func.lower(Lead.email) == key.strip().lower())
        )
        lead = result.scalar_one_or_none()
        if not lead:
            recipient_email = key.strip().lower()

    # Gather records
    messages: list[dict] = []

    if lead:
        logs = (
            await db.execute(
                select(EmailLog)
                .where(EmailLog.lead_id == lead.id)
                .order_by(EmailLog.sent_at.asc().nulls_last(), EmailLog.created_at.asc())
            )
        ).scalars().all()
        replies = (
            await db.execute(
                select(Reply)
                .where(Reply.lead_id == lead.id)
                .order_by(Reply.received_at.asc())
            )
        ).scalars().all()
    else:
        logs = (
            await db.execute(
                select(EmailLog)
                .where(EmailLog.recipient_email == recipient_email)
                .order_by(EmailLog.sent_at.asc().nulls_last(), EmailLog.created_at.asc())
            )
        ).scalars().all()
        replies = (
            await db.execute(
                select(Reply)
                .where(Reply.from_email == recipient_email)
                .order_by(Reply.received_at.asc())
            )
        ).scalars().all()

    for log in logs:
        messages.append(serialize_email_log(log))

    for reply in replies:
        messages.append(serialize_reply(reply))
        # Show the auto-response we sent back as its own outgoing message
        if reply.auto_response_sent and reply.auto_response_at and reply.auto_response_body:
            messages.append({
                "id": f"auto_{reply.id}",
                "type": "auto_response",
                "direction": "outgoing",
                "from_email": settings.EMAIL_FROM,
                "to_email": reply.from_email,
                "subject": f"Re: {reply.subject or ''}"[:500],
                "body": reply.auto_response_body,
                "status": "sent",
                "sent_at": _iso(reply.auto_response_at),
                "is_follow_up": False,
                "campaign_id": None,
            })

    def _ts(m: dict) -> str:
        return m.get("sent_at") or m.get("received_at") or ""

    messages.sort(key=_ts)

    # Conversation-level summary
    statuses = [m.get("status") for m in messages if m.get("status")]
    if not statuses:
        conversation_status = "no_activity"
    else:
        conversation_status = best_status(statuses)

    lead_info = None
    if lead:
        lead_info = {
            "id": str(lead.id),
            "name": lead.name,
            "email": lead.email,
            "headline": lead.headline,
            "status": lead.status,
            "source": lead.source,
            "priority_score": lead.priority_score,
            "profile_type": lead.profile_type,
            "location": lead.location,
            "company": lead.company,
        }
    else:
        lead_info = {
            "id": None,
            "name": recipient_email or key,
            "email": recipient_email or key,
            "headline": None,
            "status": None,
            "source": None,
            "priority_score": None,
            "profile_type": None,
            "location": None,
            "company": None,
        }

    return {
        "conversation_key": key,
        "lead": lead_info,
        "status": conversation_status,
        "sender_email": settings.EMAIL_FROM,
        "messages_count": len(messages),
        "messages": messages,
    }
