"""
Campaign routes — ports from student-intake-agent-2 campaignController.js.

Full CRUD for campaigns, plus activate/pause/sendTest/sendFollowUps/monitoring.
"""

from uuid import UUID
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.models.lead import Lead

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class CampaignCreate(BaseModel):
    name: str
    description: str | None = None
    target_type: str | None = None
    target_clusters: list[str] | None = None
    email_template: dict | None = None
    follow_up: dict | None = None
    schedule: dict | None = None
    created_by: str | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    target_type: str | None = None
    target_clusters: list[str] | None = None
    email_template: dict | None = None
    follow_up: dict | None = None
    schedule: dict | None = None
    status: str | None = None


# ── CRUD ──────────────────────────────────────────────────────────────────────


@router.get("")
async def list_campaigns(
    status: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all campaigns with optional status filter."""
    query = select(Campaign)
    if status:
        query = query.where(Campaign.status == status)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)
    result = await db.execute(
        query.order_by(Campaign.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    campaigns = result.scalars().all()
    return {"total": total, "page": page, "page_size": page_size, "data": campaigns}


@router.post("", status_code=201)
async def create_campaign(
    payload: CampaignCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new campaign."""
    campaign = Campaign(**payload.model_dump())
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single campaign by ID."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    return campaign


@router.patch("/{campaign_id}")
async def update_campaign(
    campaign_id: UUID, payload: CampaignUpdate, db: AsyncSession = Depends(get_db)
):
    """Update a campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(campaign, field, value)
    campaign.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    await db.delete(campaign)
    await db.commit()


# ── Campaign Actions ──────────────────────────────────────────────────────────


@router.post("/{campaign_id}/activate")
async def activate_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Activate a campaign (changes status to active)."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != "draft" and campaign.status != "paused":
        raise HTTPException(400, f"Cannot activate campaign with status '{campaign.status}'")

    campaign.status = "active"
    campaign.launched_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Pause an active campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    if campaign.status != "active":
        raise HTTPException(400, "Only active campaigns can be paused")

    campaign.status = "paused"
    await db.commit()
    await db.refresh(campaign)
    return campaign


@router.post("/{campaign_id}/send-test")
async def send_test_email(
    campaign_id: UUID,
    test_email: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a test email for a campaign to a specified address.
    Uses the first available lead as personalisation context,
    or falls back to dummy data if no leads exist.
    """
    from app.services.email_service import send_email, personalize_template

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    template = campaign.email_template or {}
    subject_template = template.get("subject", campaign.name)
    body_template = template.get("body", "")

    if not body_template:
        raise HTTPException(400, "Campaign has no email body template. Please set up an email template first.")

    # Try to get a real lead for personalisation context
    sample_lead_result = await db.execute(
        select(Lead).where(Lead.email.isnot(None)).limit(1)
    )
    sample_lead = sample_lead_result.scalar_one_or_none()

    # If no lead exists, create a dummy lead object for template preview
    if not sample_lead:
        class DummyLead:
            name = "Budi Santoso"
            headline = "Software Engineer di PT. Contoh"
            company = "PT. Contoh Indonesia"
            job_title = "Software Engineer"
            location = "Jakarta"
            skills = ["Python", "Machine Learning", "Data Science"]
            recommended_program = "S2 Ilmu Komputer (Master of Computer Science)"
        sample_lead = DummyLead()

    subject = personalize_template(subject_template, sample_lead)
    body = personalize_template(body_template, sample_lead)

    result = await send_email(
        to_email=test_email,
        to_name="Test Recipient",
        subject=f"[TEST] {subject}",
        body=body,
        campaign_id=campaign_id,
        lead_id=None,
        db=db,
    )

    return {
        "success": result.get("success", False),
        "message": "Test email sent successfully" if result.get("success") else "Test email logged (Resend not configured)",
        "sent_to": test_email,
        "subject": f"[TEST] {subject}",
        "tracking_id": result.get("tracking_id"),
        "note": "Email personalised using sample lead data" if sample_lead else "Email sent with dummy data",
    }


@router.post("/{campaign_id}/send-follow-ups")
async def send_campaign_follow_ups(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Send follow-up emails for leads who received the initial campaign email
    but have not replied yet. Respects the follow-up configuration
    (enabled, delay_days, max_follow_ups) set on the campaign.
    """
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    follow_up_config = campaign.follow_up or {}
    if not follow_up_config.get("enabled"):
        raise HTTPException(
            400,
            detail="Follow-ups are not enabled for this campaign. "
                   "Enable them in the campaign's follow-up settings."
        )

    from app.services.email_service import send_follow_ups
    result = await send_follow_ups(campaign_id, db)
    return {
        "campaign_id": str(campaign_id),
        "campaign_name": campaign.name,
        **result,
    }


@router.post("/{campaign_id}/send-all")
async def send_campaign_to_all(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Send the campaign email to ALL leads with a registered email address.
    Creates an EmailLog record per lead (traffic) and updates campaign stats.
    """
    from app.services.email_service import send_email

    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    template = campaign.email_template or {}
    subject = template.get("subject", campaign.name)
    body = template.get("body", "")

    if not body:
        raise HTTPException(400, "Campaign has no email body template")

    # All leads that have an email
    leads = (await db.execute(
        select(Lead).where(Lead.email.isnot(None))
    )).scalars().all()

    sent = 0
    failed = 0
    for lead in leads:
        lead_body = body.replace("{{name}}", lead.name or "there")
        result = await send_email(
            to_email=lead.email,
            to_name=lead.name or "",
            subject=subject,
            body=lead_body,
            campaign_id=campaign.id,
            lead_id=lead.id,
            db=db,
        )
        if result.get("success"):
            sent += 1
        else:
            failed += 1

    # Update campaign stats + status
    campaign.stats = {
        "total_targeted": len(leads),
        "emails_sent": sent,
        "emails_opened": 0,
        "emails_clicked": 0,
        "replies_received": 0,
        "interested": 0,
        "unsubscribed": 0,
        "bounced": 0,
    }
    if campaign.status == "draft":
        campaign.status = "active"
    await db.commit()

    return {
        "campaign_id": str(campaign_id),
        "campaign": campaign.name,
        "total_targeted": len(leads),
        "emails_sent": sent,
        "emails_failed": failed,
    }


# ── Campaign Stats ────────────────────────────────────────────────────────────


@router.get("/{campaign_id}/stats")
async def get_campaign_stats(campaign_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed stats for a campaign."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")

    # Count email logs for this campaign
    total_sent = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.status == "sent",
        )
    )
    total_opened = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.opened_at.isnot(None),
        )
    )
    total_clicked = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.clicked_at.isnot(None),
        )
    )
    total_replied = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.replied_at.isnot(None),
        )
    )
    total_bounced = await db.scalar(
        select(func.count(EmailLog.id)).where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.status == "bounced",
        )
    )

    return {
        "campaign_id": str(campaign_id),
        "campaign_name": campaign.name,
        "status": campaign.status,
        "stats": {
            "total_sent": total_sent or 0,
            "total_opened": total_opened or 0,
            "total_clicked": total_clicked or 0,
            "total_replied": total_replied or 0,
            "total_bounced": total_bounced or 0,
            "open_rate": round((total_opened or 0) / max(total_sent or 1, 1) * 100, 2),
            "click_rate": round((total_clicked or 0) / max(total_sent or 1, 1) * 100, 2),
            "reply_rate": round((total_replied or 0) / max(total_sent or 1, 1) * 100, 2),
        },
    }
