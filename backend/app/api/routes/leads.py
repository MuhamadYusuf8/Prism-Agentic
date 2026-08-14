from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin
from app.models.user import User
from app.models.lead import Lead, LeadStatus, LeadSource
from app.scrapers.alumni import parse_alumni_file, save_alumni_records
from app.services.profiling import profile_lead, profile_batch, get_profiling_stats
from app.services.clustering import cluster_leads, get_cluster_stats
from app.services.data_processor import process_and_deduplicate

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────


class LeadCreate(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    headline: str | None = None
    summary: str | None = None
    company: str | None = None
    job_title: str | None = None
    industry: str | None = None
    location: str | None = None
    education_level: str | None = None
    skills: list[str] | None = None
    source: str
    notes: str | None = None


class LeadUpdate(BaseModel):
    status: str | None = None
    priority_score: int | None = None
    profile_score: float | None = None
    profile_type: str | None = None
    notes: str | None = None
    recommended_program: str | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


# ── CRUD ──────────────────────────────────────────────────────────────────────


@router.get("")
async def list_leads(
    status: str | None = None,
    source: str | None = None,
    profile_type: str | None = None,
    field: str | None = None,
    search: str | None = None,
    is_cs_related: bool | None = None,
    data_quality: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List leads with filtering, search, and pagination."""
    query = select(Lead)

    if status:
        query = query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
    if profile_type:
        query = query.where(Lead.profile_type == profile_type)
    if field:
        query = query.where(Lead.field == field)
    if is_cs_related is not None:
        query = query.where(Lead.is_computer_science_related == is_cs_related)
    if data_quality:
        query = query.where(Lead.data_quality == data_quality)
    if search:
        query = query.where(
            or_(
                Lead.name.ilike(f"%{search}%"),
                Lead.company.ilike(f"%{search}%"),
                Lead.job_title.ilike(f"%{search}%"),
                Lead.headline.ilike(f"%{search}%"),
                Lead.email.ilike(f"%{search}%"),
            )
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)
    result = await db.execute(
        query.order_by(Lead.priority_score.desc().nulls_last(), Lead.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    leads = result.scalars().all()
    return {"total": total, "page": page, "page_size": page_size, "data": leads}


@router.post("", status_code=201)
async def create_lead(
    payload: LeadCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new lead."""
    lead = Lead(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.get("/interactions/followups")
async def follow_up_reminders(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get leads that need a LinkedIn follow-up (contacted, no reply in 7 days)."""
    from app.services.interaction_monitor import get_follow_up_reminders
    reminders = await get_follow_up_reminders(db)
    return {"reminders": reminders, "count": len(reminders)}


class EmailDiscoveryRequest(BaseModel):
    lead_ids: list[str] | None = None  # None = discover for leads without email


@router.post("/email-discovery/batch")
async def batch_email_discovery(
    payload: EmailDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
):
    """Discover emails for leads without one, using Serper + optional Hunter.io."""
    from app.services.email_discovery import discover_email

    if payload.lead_ids:
        leads = (await db.execute(select(Lead).where(Lead.id.in_(payload.lead_ids)))).scalars().all()
    else:
        leads = (
            await db.execute(
                select(Lead)
                .where(Lead.email.is_(None))
                .order_by(Lead.created_at.desc())
                .limit(50)
            )
        ).scalars().all()

    results = []
    for lead in leads:
        company = lead.company
        # Try to derive a domain from raw_data if available
        website = None
        if lead.raw_data and isinstance(lead.raw_data, dict):
            website = lead.raw_data.get("website") or lead.raw_data.get("company_website")

        result = await discover_email(lead.name, company=company, website=website)
        if result.get("email"):
            lead.email = result["email"]
            results.append({
                "lead_id": str(lead.id),
                "name": lead.name,
                "email": result["email"],
                "confidence": result["confidence"],
                "source": result["source"],
            })
        else:
            results.append({
                "lead_id": str(lead.id),
                "name": lead.name,
                "email": None,
                "confidence": 0,
                "source": None,
            })

    await db.commit()
    found = sum(1 for r in results if r["email"])
    return {"total": len(results), "found": found, "results": results}


@router.get("/{lead_id}")
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single lead by ID."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return lead


@router.patch("/{lead_id}")
async def update_lead(lead_id: UUID, payload: LeadUpdate, db: AsyncSession = Depends(get_db)):
    """Update a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(lead, field, value)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.delete("/{lead_id}", status_code=204)
async def delete_lead(
    lead_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Delete a lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    await db.delete(lead)
    await db.commit()


# ── Profiling ─────────────────────────────────────────────────────────────────


@router.post("/{lead_id}/profile")
async def profile_single_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Run profiling pipeline on a single lead."""
    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    result = await profile_lead(lead, db)
    return result


@router.post("/profile/batch")
async def profile_multiple_leads(
    lead_ids: list[UUID],
    db: AsyncSession = Depends(get_db),
):
    """Run profiling pipeline on multiple leads."""
    result = await profile_batch(lead_ids, db)
    return result


@router.get("/stats/profiling")
async def profiling_statistics(db: AsyncSession = Depends(get_db)):
    """Get profiling statistics."""
    stats = await get_profiling_stats(db)
    return stats


# ── Clustering ────────────────────────────────────────────────────────────────


@router.post("/cluster")
async def run_clustering(
    lead_ids: list[UUID] | None = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Run clustering on leads (optionally filtered by IDs)."""
    result = await cluster_leads(db, lead_ids)
    return result


@router.get("/stats/clusters")
async def cluster_statistics(db: AsyncSession = Depends(get_db)):
    """Get cluster statistics."""
    stats = await get_cluster_stats(db)
    return stats


# ── Alumni import ─────────────────────────────────────────────────────────────


@router.post("/import/alumni")
async def import_alumni(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Import alumni data from CSV or Excel.

    Accepted columns (Indonesian or English names):
      name/nama, email, phone/no_hp, company/perusahaan,
      job_title/jabatan, education_level/pendidikan,
      location/kota, notes/catatan
    """
    if not file.filename:
        raise HTTPException(400, "No file provided")

    allowed = (".csv", ".xlsx", ".xls")
    if not file.filename.lower().endswith(allowed):
        raise HTTPException(400, f"File must be one of: {', '.join(allowed)}")

    content = await file.read()
    result = parse_alumni_file(content, file.filename)

    if not result.records:
        raise HTTPException(422, {
            "message": "No valid records found",
            "errors": result.errors[:10],
        })

    saved = await save_alumni_records(result.records, db)

    return {
        "filename": file.filename,
        "total_rows": result.total_rows,
        "imported": saved,
        "skipped": result.skipped,
        "warnings": result.errors[:10],
    }


# ── LinkedIn Interaction Monitoring ───────────────────────────────────────────


class InteractionCreate(BaseModel):
    interaction_type: str  # profile_view | connection_request | connection_accepted | message_sent | reply_received | follow_up_sent | note
    notes: str | None = None
    content: str | None = None


@router.get("/{lead_id}/interactions")
async def get_lead_interactions(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the LinkedIn interaction history for a lead."""
    from app.services.interaction_monitor import get_interactions

    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")
    return {"interactions": get_interactions(lead)}


@router.post("/{lead_id}/interactions", status_code=201)
async def create_lead_interaction(
    lead_id: UUID,
    payload: InteractionCreate,
    db: AsyncSession = Depends(get_db),
):
    """Log a LinkedIn interaction on a lead."""
    from app.services.interaction_monitor import log_interaction

    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    allowed = {
        "profile_view", "connection_request", "connection_accepted",
        "message_sent", "reply_received", "follow_up_sent", "note",
    }
    if payload.interaction_type not in allowed:
        raise HTTPException(422, f"interaction_type must be one of: {', '.join(sorted(allowed))}")

    interaction = await log_interaction(
        lead,
        payload.interaction_type,
        db,
        notes=payload.notes,
        content=payload.content,
    )
    return interaction


@router.post("/{lead_id}/find-email")
async def find_lead_email(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Discover an email for a single lead (Serper + optional Hunter.io)."""
    from app.services.email_discovery import discover_email

    lead = await db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, "Lead not found")

    if lead.email:
        return {"email": lead.email, "confidence": 100, "source": "existing", "candidates": []}

    website = None
    if lead.raw_data and isinstance(lead.raw_data, dict):
        website = lead.raw_data.get("website") or lead.raw_data.get("company_website")

    result = await discover_email(lead.name, company=lead.company, website=website)

    if result.get("email"):
        lead.email = result["email"]
        await db.commit()
        await db.refresh(lead)

    result["lead_id"] = str(lead.id)
    result["name"] = lead.name
    return result
