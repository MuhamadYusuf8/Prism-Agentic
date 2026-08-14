import asyncio
from app.core.celery_app import celery_app
from app.core.database import AsyncSessionLocal


@celery_app.task(name="app.workers.scrape_tasks.run_linkedin_scrape", bind=True, max_retries=3)
def run_linkedin_scrape(self, search_queries=None, max_profiles=50):
    """Celery task: scrape LinkedIn CS profiles via Google search."""
    from app.scrapers.linkedin import scrape_linkedin_cs_profiles, save_linkedin_profiles

    async def _run():
        async with AsyncSessionLocal() as db:
            profiles = await scrape_linkedin_cs_profiles(search_queries, max_profiles)
            return await save_linkedin_profiles(profiles, db)

    try:
        count = asyncio.run(_run())
        return {"status": "ok", "saved": count}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=120)
