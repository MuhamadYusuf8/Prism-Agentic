"""
Celery email tasks — background processing for campaign email dispatch.

These tasks run asynchronously via the Celery worker so the HTTP request
returns immediately while emails are delivered in the background.
"""

import asyncio
from datetime import datetime, timezone

from app.core.celery_app import celery_app


# ── Send Bulk Campaign ─────────────────────────────────────────────────────────


@celery_app.task(
    name="app.workers.email_tasks.dispatch_campaign",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def dispatch_campaign(self, campaign_id: str):
    """
    Background task: send a campaign email to all targeted leads.

    Handles its own async event loop so it can reuse the existing
    async email_service and database session.
    """
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.email_service import send_campaign
        import uuid

        async with AsyncSessionLocal() as db:
            result = await send_campaign(uuid.UUID(campaign_id), db)
            return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run())
        loop.close()
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


# ── Send Bulk Outreach to Specific Leads ──────────────────────────────────────


@celery_app.task(
    name="app.workers.email_tasks.send_bulk_outreach",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def send_bulk_outreach(self, campaign_id: str, lead_ids: list[str]):
    """
    Background task: send a campaign email to a specific subset of leads.
    Used when the recruiter selects individual leads to target.
    """
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.email_service import send_email, personalize_template
        from app.models.campaign import Campaign
        from app.models.lead import Lead
        from sqlalchemy import select
        import uuid

        async with AsyncSessionLocal() as db:
            campaign = await db.get(Campaign, uuid.UUID(campaign_id))
            if not campaign:
                return {"error": "Campaign not found"}

            template = campaign.email_template or {}
            subject_template = template.get("subject", campaign.name)
            body_template = template.get("body", "")

            if not body_template:
                return {"error": "Campaign has no email body template"}

            # Fetch selected leads
            result = await db.execute(
                select(Lead).where(
                    Lead.id.in_([uuid.UUID(lid) for lid in lead_ids]),
                    Lead.email.isnot(None),
                )
            )
            leads = result.scalars().all()

            sent, failed, errors = 0, 0, []
            for lead in leads:
                try:
                    subject = personalize_template(subject_template, lead)
                    body = personalize_template(body_template, lead)
                    send_result = await send_email(
                        to_email=lead.email,
                        to_name=lead.name or "",
                        subject=subject,
                        body=body,
                        campaign_id=campaign.id,
                        lead_id=lead.id,
                        db=db,
                    )
                    if send_result.get("success"):
                        sent += 1
                        # Update lead status
                        if lead.status not in ("contacted", "interested", "applied", "enrolled"):
                            lead.status = "contacted"
                            lead.last_contacted_at = datetime.now(timezone.utc)
                    else:
                        failed += 1
                        errors.append({"lead_id": str(lead.id), "error": send_result.get("error")})
                except Exception as e:
                    failed += 1
                    errors.append({"lead_id": str(lead.id), "error": str(e)})

            # Update campaign stats
            if campaign.stats is None:
                campaign.stats = {}
            campaign.stats["emails_sent"] = (campaign.stats.get("emails_sent", 0) + sent)
            await db.commit()

            return {
                "campaign_id": campaign_id,
                "total": len(leads),
                "sent": sent,
                "failed": failed,
                "errors": errors,
            }

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run())
        loop.close()
        return result
    except Exception as exc:
        raise self.retry(exc=exc)


# ── Send Follow-Up Emails ──────────────────────────────────────────────────────


@celery_app.task(
    name="app.workers.email_tasks.dispatch_follow_ups",
    bind=True,
    max_retries=3,
    default_retry_delay=120,
)
def dispatch_follow_ups(self, campaign_id: str):
    """
    Background task: send follow-up emails for a campaign.
    Called by Celery Beat scheduler or manually via the API.
    """
    async def _run():
        from app.core.database import AsyncSessionLocal
        from app.services.email_service import send_follow_ups
        import uuid

        async with AsyncSessionLocal() as db:
            result = await send_follow_ups(uuid.UUID(campaign_id), db)
            return result

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run())
        loop.close()
        return result
    except Exception as exc:
        raise self.retry(exc=exc)
