import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import AsyncSessionLocal
from app.core.config import settings as app_settings
from app.core.auth import require_admin
from app.models.user import User
from app.api.routes.settings import _settings_store
from app.scrapers.linkedin import scrape_linkedin_cs_stream, save_linkedin_profiles
from app.scrapers.linkedin_detail import batch_enrich_profiles
from app.services.syllabus_matcher import compute_syllabus_match, run_syllabus_matching_on_all_leads
from app.services.email_discovery import discover_email

router = APIRouter()


class ScrapeRequest(BaseModel):
    search_queries: list[str] | None = None
    max_profiles: int = 50
    enrich_details: bool = True  # Whether to run Phase 2
    field: str | None = None  # computer_science | management | law


class EnrichRequest(BaseModel):
    lead_ids: list[str] | None = None  # None = enrich all unenriched leads


# ── SSE Two-Phase streaming scrape ────────────────────────────────────────────

@router.post("/linkedin/stream")
async def stream_linkedin_scrape(
    payload: ScrapeRequest,
    _: User = Depends(require_admin),
):
    """
    Two-phase LinkedIn scraping as Server-Sent Events.

    Phase 1: Serper Google Search → discover profile URLs → save basic data
    Phase 2: (optional) Authenticated session → enrich with full profile details
    """
    collected_profiles: list[dict] = []
    profile_urls: list[str] = []

    async def event_generator():
        try:
            # ═══ PHASE 1: Serper Discovery ═══
            yield f"data: {json.dumps({'type': 'phase_1_start'})}\n\n"

            async for event in scrape_linkedin_cs_stream(
                payload.search_queries, payload.max_profiles
            ):
                if event["type"] == "profile":
                    collected_profiles.append(event["profile"])
                    profile_url = (event["profile"] or {}).get("linkedin_url")
                    if profile_url:
                        profile_urls.append(profile_url)
                yield f"data: {json.dumps(event)}\n\n"

            # Save Phase 1 results (reports new vs duplicate vs failed)
            save_result = {"inserted": 0, "updated": 0, "failed": 0, "duplicates": 0, "total": 0}
            if collected_profiles:
                async with AsyncSessionLocal() as db:
                    save_result = await save_linkedin_profiles(collected_profiles, db, field=payload.field)
            yield f"data: {json.dumps({'type': 'saved', **save_result})}\n\n"

            yield f"data: {json.dumps({
                'type': 'phase_1_done',
                'profiles_found': len(collected_profiles),
                'saved': save_result['inserted'],
                'inserted': save_result['inserted'],
                'updated': save_result['updated'],
                'duplicates': save_result['duplicates'],
                'failed': save_result['failed'],
            })}\n\n"

            # ═══ PHASE 2: Email Discovery ═══
            if collected_profiles:
                yield f"data: {json.dumps({'type': 'phase_2_start', 'total_profiles': len(collected_profiles)})}\n\n"

                email_found = 0
                email_failed = 0

                for profile in collected_profiles:
                    name = (profile or {}).get("name", "")
                    try:
                        result = await discover_email(name, (profile or {}).get("company"))
                        email = result.get("email")
                        profile_url = (profile or {}).get("linkedin_url")
                        if email and profile_url:
                            await _save_lead_email(
                                profile_url,
                                email,
                                result.get("confidence", 0),
                                result.get("source"),
                            )
                            email_found += 1
                            yield f"data: {json.dumps({
                                'type': 'email_found',
                                'name': name,
                                'email': email,
                                'confidence': result.get('confidence', 0),
                                'source': result.get('source'),
                                'progress': {'found': email_found, 'total': len(collected_profiles)},
                            })}\n\n"
                        else:
                            email_failed += 1
                            yield f"data: {json.dumps({
                                'type': 'email_skip',
                                'name': name,
                                'progress': {'found': email_found, 'total': len(collected_profiles)},
                            })}\n\n"
                    except Exception as exc:
                        email_failed += 1
                        yield f"data: {json.dumps({
                            'type': 'email_skip',
                            'name': name,
                            'error': str(exc),
                            'progress': {'found': email_found, 'total': len(collected_profiles)},
                        })}\n\n"

                    await asyncio.sleep(0.2)

                yield f"data: {json.dumps({
                    'type': 'phase_2_done',
                    'found': email_found,
                    'failed': email_failed,
                    'total': len(collected_profiles),
                })}\n\n"

            # ═══ Syllabus Matching ═══
            try:
                async with AsyncSessionLocal() as db:
                    match_result = await run_syllabus_matching_on_all_leads(db)
                yield f"data: {json.dumps({
                    'type': 'syllabus_matched',
                    'total': match_result.get('updated', 0),
                })}\n\n"
            except Exception:
                pass

            yield f"data: {json.dumps({'type': 'done', 'total_saved': save_result['inserted']})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Helper: stream enrich results one by one ───────────────────────────────────

async def _enrich_stream(profile_urls: list[str], li_at_cookie: str):
    """Generator that yields enrich results one at a time for SSE streaming."""
    results = await batch_enrich_profiles(profile_urls, li_at_cookie)
    for result in results:
        yield result


# ── Helper: save enriched data to DB ───────────────────────────────────────────

async def _save_enriched_data(profile_url: str, data: dict):
    """Update the lead record with enriched Phase 2 data."""
    from sqlalchemy import select, text
    from app.models.lead import Lead

    async with AsyncSessionLocal() as db:
        # Find lead by linkedin_url
        result = await db.execute(
            select(Lead).where(Lead.linkedin_url == profile_url)
        )
        lead = result.scalar_one_or_none()
        if not lead:
            return

        # Update fields if enriched data is available
        if data.get("skills"):
            # Merge with existing skills
            existing = lead.skills or []
            merged = list(set(existing + data["skills"]))
            lead.skills = merged

        if data.get("headline"):
            lead.headline = data["headline"]

        if data.get("summary"):
            lead.summary = data["summary"]

        if data.get("education"):
            lead.education = data["education"]

        if data.get("experience"):
            lead.experience = data["experience"]

        if data.get("location"):
            lead.location = data["location"]

        if data.get("industry"):
            lead.industry = data["industry"]

        lead.status = "profiled"

        # Run syllabus matching on this lead
        lead_dict = {
            "skills": lead.skills,
            "job_title": lead.job_title,
            "headline": lead.headline,
            "summary": lead.summary,
            "raw_data": lead.raw_data,
        }
        match = compute_syllabus_match(lead_dict)
        lead.syllabus_confidence = match["syllabus_confidence"]
        lead.syllabus_scores = match["syllabus_scores"]
        lead.syllabus_matched_subjects = match["syllabus_matched_subjects"]
        lead.syllabus_top_match = match["syllabus_top_match"]

        await db.commit()


# ── Helper: save discovered email to DB ─────────────────────────────────────────

async def _save_lead_email(profile_url: str, email: str, confidence: int, source: str | None):
    """Attach a discovered email to the lead that owns the given LinkedIn URL."""
    from sqlalchemy import select
    from app.models.lead import Lead

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Lead).where(Lead.linkedin_url == profile_url))
        lead = result.scalar_one_or_none()
        if not lead:
            return
        from datetime import datetime, timezone
        lead.email = email
        if lead.raw_data and isinstance(lead.raw_data, dict):
            lead.raw_data["email_discovery"] = {
                "confidence": confidence,
                "source": source,
                "discovered_at": datetime.now(timezone.utc).isoformat(),
            }
        await db.commit()


# ── Batch Enrichment Endpoint ──────────────────────────────────────────────────

@router.post("/linkedin/enrich")
async def enrich_linkedin_leads(payload: EnrichRequest):
    """
    Enrich existing leads with Phase 2 detail scraping.
    If lead_ids is empty, enriches all leads with linkedin_url but no skills.
    """
    from sqlalchemy import select
    from app.models.lead import Lead

    li_at = _settings_store.get("linkedin", {}).get("li_at", "") or app_settings.LINKEDIN_LI_AT
    if not li_at:
        raise HTTPException(400, "LinkedIn session cookie (li_at) not set. Add it in Settings → LinkedIn Scraper.")

    async with AsyncSessionLocal() as db:
        if payload.lead_ids:
            leads = await db.execute(
                select(Lead).where(Lead.id.in_(payload.lead_ids))
            )
            leads = leads.scalars().all()
        else:
            # Find leads that have linkedin_url but no detailed data yet
            leads = await db.execute(
                select(Lead).where(
                    Lead.linkedin_url.isnot(None),
                    Lead.skills.is_(None),
                ).order_by(Lead.created_at.desc()).limit(50)
            )
            leads = leads.scalars().all()

    if not leads:
        return {"enriched": 0, "total": 0, "message": "No leads to enrich"}

    profile_urls = [lead.linkedin_url for lead in leads if lead.linkedin_url]
    results = await batch_enrich_profiles(profile_urls, li_at)

    enriched_count = 0
    for result in results:
        if result["success"] and result.get("data"):
            await _save_enriched_data(result["profile_url"], result["data"])
            enriched_count += 1

    return {
        "enriched": enriched_count,
        "total": len(profile_urls),
        "failed": len(profile_urls) - enriched_count,
    }


# ── Debug endpoints ────────────────────────────────────────────────────────────


# ── Debug endpoints ────────────────────────────────────────────────────────────

@router.get("/debug/search")
async def debug_search(q: str = 'site:linkedin.com/in "software engineer" Indonesia'):
    """Test Serper.dev for a single query — returns extracted profile objects."""
    import httpx
    from app.scrapers.linkedin import _serper_search_profiles
    from app.core.config import settings
    from dataclasses import asdict

    if not settings.SERPER_API_KEY:
        return {"error": "SERPER_API_KEY not set in .env"}

    async with httpx.AsyncClient() as client:
        profiles = await _serper_search_profiles(
            client, q, settings.SERPER_API_KEY, max_results=10
        )
    return {
        "query": q,
        "profiles_found": len(profiles),
        "profiles": [asdict(p) for p in profiles],
    }


# ── Stats ──────────────────────────────────────────────────────────────────────

@router.get("/stats")
async def scrape_stats():
    from sqlalchemy import text
    async with AsyncSessionLocal() as db:
        leads_count   = await db.scalar(text("SELECT COUNT(*) FROM leads"))
        linkedin_count = await db.scalar(text("SELECT COUNT(*) FROM leads WHERE source = 'linkedin'"))
        alumni_count   = await db.scalar(text("SELECT COUNT(*) FROM leads WHERE source = 'alumni'"))
        by_title = await db.execute(text("""
            SELECT job_title, COUNT(*) as c FROM leads
            WHERE source = 'linkedin' AND job_title IS NOT NULL
            GROUP BY job_title ORDER BY c DESC LIMIT 10
        """))
    return {
        "total_leads": leads_count,
        "linkedin_leads": linkedin_count,
        "alumni_leads": alumni_count,
        "top_job_titles": [{"title": r[0], "count": r[1]} for r in by_title],
    }
