"""
Run syllabus matching on all leads in the database.
Usage: python scripts/run_syllabus_matching.py
"""
import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.stdout.reconfigure(encoding='utf-8')

from sqlalchemy import select, text
from app.core.database import AsyncSessionLocal
from app.models.lead import Lead
from app.services.syllabus_matcher import compute_syllabus_match


async def main():
    # First ensure new columns exist (add if missing) - one statement at a time
    async with AsyncSessionLocal() as session:
        for stmt in [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_confidence FLOAT",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_scores JSONB",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_matched_subjects JSONB",
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS syllabus_top_match VARCHAR(255)",
        ]:
            try:
                await session.execute(text(stmt))
            except Exception:
                pass  # column may already exist
        await session.commit()
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Lead))
        leads = result.scalars().all()
        print(f"Found {len(leads)} leads to process.\n")

        updated = 0
        for lead in leads:
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

            # Blend priority score with syllabus confidence
            old_score = lead.priority_score or 0
            lead.priority_score = round((old_score * 0.4 + match["syllabus_confidence"] * 0.6))
            
            updated += 1

            # Print result for this lead
            matched = match["syllabus_matched_subjects"]
            matched_str = ", ".join(matched[:3]) if matched else "none"
            print(f"  [{lead.name:30s}] conf={match['syllabus_confidence']:5.1f}  top={str(match['syllabus_top_match'] or '-'):30s}  matched=[{matched_str}]")

        await session.commit()
        print(f"\n✅ Updated {updated} leads with syllabus matching scores.")


if __name__ == "__main__":
    asyncio.run(main())
