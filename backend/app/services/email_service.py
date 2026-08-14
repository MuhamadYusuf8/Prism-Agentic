"""
Email Service — ports from student-intake-agent-2 emailService.js.

Handles email sending with tracking (pixel + link tracking),
campaign dispatch, follow-up sending, and template personalization.
"""

import uuid
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.email_log import EmailLog


# ── Template Personalization ───────────────────────────────────────────────────


def personalize_template(template: str | dict, lead: Lead) -> str:
    """
    Personalize email template with lead data.
    Supports variables: {{name}}, {{firstName}}, {{program}}, {{university}},
    {{location}}, {{skills}}, {{headline}}
    """
    if isinstance(template, dict):
        template = template.get("body", "")

    first_name = lead.name.split(" ")[0] if lead.name else "there"
    skills_str = ", ".join(lead.skills[:5]) if lead.skills else ""

    variables = {
        "name": lead.name or "Prospective Student",
        "firstName": first_name,
        "program": lead.recommended_program or "your chosen program",
        "university": "President University",
        "location": lead.location or "your area",
        "skills": skills_str,
        "headline": lead.headline or "",
    }

    result = template
    for key, value in variables.items():
        result = result.replace("{{" + key + "}}", str(value))

    return result


# ── Tracking ───────────────────────────────────────────────────────────────────


def add_tracking_pixel(body: str, tracking_id: str) -> str:
    """Add tracking pixel to email body."""
    pixel_url = f"{settings.BASE_URL or 'http://localhost:8000'}/api/tracking/open/{tracking_id}"
    pixel = f'<img src="{pixel_url}" width="1" height="1" style="display:none;" alt=""/>'
    return body + pixel


def add_link_tracking(body: str, tracking_id: str) -> str:
    """Rewrite links in email body to add tracking."""
    tracking_base = f"{settings.BASE_URL or 'http://localhost:8000'}/api/tracking/click/{tracking_id}"

    def rewrite_link(match):
        href = match.group(1)
        encoded_href = href.replace("&", "%26").replace("?", "%3F")
        return f'<a href="{tracking_base}?url={encoded_href}"'

    return re.sub(r'<a\s+href="([^"]+)"', rewrite_link, body)


# ── Email Sending ──────────────────────────────────────────────────────────────


async def send_email(
    to_email: str,
    to_name: str,
    subject: str,
    body: str,
    campaign_id: uuid.UUID | None = None,
    lead_id: uuid.UUID | None = None,
    is_follow_up: bool = False,
    follow_up_number: int = 0,
    db: AsyncSession | None = None,
) -> dict:
    """
    Send an email via Resend API with tracking.
    Falls back to logging if Resend is not configured.
    """
    tracking_id = str(uuid.uuid4())

    # Add tracking
    body_with_tracking = add_tracking_pixel(body, tracking_id)
    body_with_tracking = add_link_tracking(body_with_tracking, tracking_id)

    # Create email log
    email_log = EmailLog(
        campaign_id=campaign_id,
        lead_id=lead_id,
        recipient_email=to_email,
        recipient_name=to_name,
        subject=subject,
        body=body_with_tracking,
        tracking_id=tracking_id,
        status="pending",
        is_follow_up=is_follow_up,
        follow_up_number=follow_up_number,
    )

    if db:
        db.add(email_log)
        await db.commit()
        await db.refresh(email_log)

    # Try sending via Resend if API key is configured
    if settings.RESEND_API_KEY:
        try:
            import resend
            resend.api_key = settings.RESEND_API_KEY

            params = {
                "from": settings.EMAIL_FROM,
                "to": [to_email],
                "subject": subject,
                "html": body_with_tracking,
            }

            response = resend.Emails.send(params)
            email_log.status = "sent"
            email_log.sent_at = datetime.now(timezone.utc)

            if db:
                await db.commit()

            return {
                "success": True,
                "tracking_id": tracking_id,
                "email_log_id": str(email_log.id) if email_log.id else None,
                "response": response,
            }

        except Exception as e:
            email_log.status = "failed"
            email_log.error_message = str(e)
            if db:
                await db.commit()

            return {
                "success": False,
                "tracking_id": tracking_id,
                "error": str(e),
            }
    else:
        # No Resend configured — log only
        email_log.status = "logged"
        if db:
            await db.commit()

        return {
            "success": True,
            "tracking_id": tracking_id,
            "email_log_id": str(email_log.id) if email_log.id else None,
            "message": "Email logged (Resend not configured)",
        }


# ── Campaign Dispatch ──────────────────────────────────────────────────────────


async def send_campaign(
    campaign_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Send a campaign to all targeted leads."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return {"success": False, "error": "Campaign not found"}

    # Get targeted leads
    query = select(Lead).where(
        Lead.is_active == True,
        Lead.status.in_(["profiled", "clustered", "contacted"]),
    )

    # Filter by target clusters if specified
    if campaign.target_clusters:
        query = query.where(Lead.cluster_id.in_(campaign.target_clusters))

    # Filter by target type
    if campaign.target_type and campaign.target_type != "all":
        query = query.where(Lead.profile_type == campaign.target_type)

    result = await db.execute(query)
    leads = result.scalars().all()

    if not leads:
        return {"success": True, "sent": 0, "message": "No matching leads found"}

    template = campaign.email_template or {}
    subject_template = template.get("subject", "Information from President University")
    body_template = template.get("body", "")

    results = {"total": len(leads), "sent": 0, "failed": 0, "errors": []}

    for lead in leads:
        try:
            subject = personalize_template(subject_template, lead)
            body = personalize_template(body_template, lead)

            send_result = await send_email(
                to_email=lead.email or "",
                to_name=lead.name or "",
                subject=subject,
                body=body,
                campaign_id=campaign_id,
                lead_id=lead.id,
                db=db,
            )

            if send_result["success"]:
                results["sent"] += 1
                # Update lead status
                if lead.status not in ("contacted", "interested", "applied", "enrolled"):
                    from app.models.lead import LeadStatus
                    lead.status = LeadStatus.CONTACTED.value
                    lead.last_contacted_at = datetime.now(timezone.utc)
            else:
                results["failed"] += 1
                results["errors"].append({"lead_id": str(lead.id), "error": send_result.get("error")})

        except Exception as e:
            results["failed"] += 1
            results["errors"].append({"lead_id": str(lead.id), "error": str(e)})

    # Update campaign stats
    if campaign.stats is None:
        campaign.stats = {}
    campaign.stats["emails_sent"] = (campaign.stats.get("emails_sent", 0) + results["sent"])
    campaign.stats["total_targeted"] = len(leads)

    await db.commit()
    return results


async def send_follow_ups(
    campaign_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    """Send follow-up emails for a campaign based on follow-up configuration."""
    campaign = await db.get(Campaign, campaign_id)
    if not campaign:
        return {"success": False, "error": "Campaign not found"}

    follow_up_config = campaign.follow_up or {}
    if not follow_up_config.get("enabled"):
        return {"success": True, "sent": 0, "message": "Follow-ups not enabled"}

    max_follow_ups = follow_up_config.get("max_follow_ups", 3)
    delay_days = follow_up_config.get("delay_days", 7)

    # Find leads who received the campaign but haven't replied
    # and haven't reached max follow-ups
    subquery = (
        select(
            EmailLog.lead_id,
            func.count(EmailLog.id).label("follow_up_count"),
            func.max(EmailLog.sent_at).label("last_sent"),
        )
        .where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.is_follow_up == True,
        )
        .group_by(EmailLog.lead_id)
    ).subquery()

    # Leads who received initial email but no follow-up yet
    initial_recipients = await db.execute(
        select(EmailLog.lead_id)
        .where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.is_follow_up == False,
            EmailLog.status == "sent",
        )
    )
    initial_lead_ids = {row[0] for row in initial_recipients if row[0]}

    # Get leads who already have follow-ups
    followed_up = await db.execute(
        select(EmailLog.lead_id)
        .where(
            EmailLog.campaign_id == campaign_id,
            EmailLog.is_follow_up == True,
        )
    )
    followed_up_ids = {row[0] for row in followed_up if row[0]}

    # Leads who need follow-ups (received initial but haven't had follow-ups yet)
    pending_lead_ids = initial_lead_ids - followed_up_ids

    if not pending_lead_ids:
        return {"success": True, "sent": 0, "message": "No leads pending follow-up"}

    # Get lead details
    result = await db.execute(
        select(Lead).where(Lead.id.in_(list(pending_lead_ids)))
    )
    leads = result.scalars().all()

    follow_up_template = follow_up_config.get("template", {})
    subject_template = follow_up_template.get("subject", "Follow-Up: {{name}}")
    body_template = follow_up_template.get("body", "")

    results = {"total": len(leads), "sent": 0, "failed": 0}

    for lead in leads:
        try:
            # Count existing follow-ups for this lead
            count_result = await db.execute(
                select(func.count(EmailLog.id))
                .where(
                    EmailLog.campaign_id == campaign_id,
                    EmailLog.lead_id == lead.id,
                    EmailLog.is_follow_up == True,
                )
            )
            follow_up_count = count_result.scalar() or 0

            if follow_up_count >= max_follow_ups:
                continue

            subject = personalize_template(subject_template, lead)
            body = personalize_template(body_template, lead)

            send_result = await send_email(
                to_email=lead.email or "",
                to_name=lead.name or "",
                subject=subject,
                body=body,
                campaign_id=campaign_id,
                lead_id=lead.id,
                is_follow_up=True,
                follow_up_number=follow_up_count + 1,
                db=db,
            )

            if send_result["success"]:
                results["sent"] += 1
        except Exception as e:
            results["failed"] += 1

    await db.commit()
    return results
