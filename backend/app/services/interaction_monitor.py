"""
Interaction Monitoring Service — tracks LinkedIn outreach per scraped profile.

Because emails are rarely available for scraped LinkedIn profiles, this service
monitors the LinkedIn-native outreach lifecycle instead:

    new → contacted → replied → interested → applied/enrolled
                    └─ not_interested / unsubscribed

Interactions are stored in the lead's `communication` JSON field under
`linkedin_interactions`, so no schema migration is required.

Interaction types:
    - profile_view          (recruiter opened the profile)
    - connection_request    (connection request sent)
    - connection_accepted   (they accepted)
    - message_sent          (message / InMail sent)
    - reply_received        (they replied — content captured)
    - follow_up_sent        (a follow-up was sent)
    - note                  (freeform recruiter note)
"""

import uuid
from datetime import datetime, timezone, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead

# Statuses that represent an active conversation (need follow-up if idle)
_ACTIVE_STATUSES = {"contacted", "replied", "interested"}

# How many days of silence before a follow-up is due
FOLLOW_UP_DAYS = 7


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_communication(lead: Lead) -> dict:
    """Ensure lead.communication is a usable dict."""
    comm = lead.communication
    if not comm or not isinstance(comm, dict):
        comm = {}
    if "linkedin_interactions" not in comm or not isinstance(comm.get("linkedin_interactions"), list):
        comm["linkedin_interactions"] = []
    return comm


def get_interactions(lead: Lead) -> list[dict]:
    """Return the interaction history for a lead, newest first."""
    comm = _get_communication(lead)
    interactions = list(comm.get("linkedin_interactions", []))
    interactions.sort(key=lambda x: x.get("at", ""), reverse=True)
    return interactions


async def log_interaction(
    lead: Lead,
    interaction_type: str,
    db: AsyncSession,
    *,
    notes: str | None = None,
    content: str | None = None,
) -> dict:
    """
    Log a LinkedIn interaction on a lead and update its status accordingly.

    Returns the created interaction dict.
    """
    comm = _get_communication(lead)

    interaction = {
        "id": str(uuid.uuid4()),
        "type": interaction_type,
        "at": _now_iso(),
        "notes": notes,
        "content": content,
    }
    comm["linkedin_interactions"].append(interaction)
    comm["last_contacted_at"] = interaction["at"]
    lead.last_contacted_at = datetime.now(timezone.utc)  # sync DB column for follow-up queries

    # Update lead status + interested flag based on interaction type
    if interaction_type == "connection_request":
        lead.status = "contacted"
    elif interaction_type == "connection_accepted":
        lead.status = "contacted"  # still waiting for reply
    elif interaction_type == "message_sent":
        lead.status = "contacted"
    elif interaction_type == "reply_received":
        lead.status = "replied"
        comm["interested"] = True
        comm["interested_at"] = interaction["at"]
        if content:
            comm["last_reply_content"] = content
    elif interaction_type == "follow_up_sent":
        lead.status = "contacted"
    elif interaction_type == "note":
        pass  # status unchanged

    lead.communication = comm
    await db.commit()
    await db.refresh(lead)
    return interaction


async def get_follow_up_reminders(db: AsyncSession, due_days: int = FOLLOW_UP_DAYS) -> list[dict]:
    """
    Find leads that have been contacted but have no reply within `due_days`,
    or whose last contact was more than `due_days` ago without a reply.

    Returns list of dicts: {id, name, linkedin_url, last_contacted_at, days_since}.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=due_days)

    result = await db.execute(
        select(Lead).where(
            Lead.status.in_(_ACTIVE_STATUSES),
            Lead.last_contacted_at.isnot(None),
        )
    )
    leads = result.scalars().all()

    reminders = []
    for lead in leads:
        last = lead.last_contacted_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        if last < cutoff:
            # Only remind if the last interaction wasn't a reply
            comm = _get_communication(lead)
            last_interaction = None
            if comm.get("linkedin_interactions"):
                last_interaction = comm["linkedin_interactions"][-1]
            if last_interaction and last_interaction.get("type") == "reply_received":
                continue  # already replied — no follow-up needed

            reminders.append({
                "id": str(lead.id),
                "name": lead.name,
                "linkedin_url": lead.linkedin_url,
                "status": lead.status,
                "last_contacted_at": last.isoformat(),
                "days_since": (datetime.now(timezone.utc) - last).days,
            })

    reminders.sort(key=lambda r: r["days_since"], reverse=True)
    return reminders
