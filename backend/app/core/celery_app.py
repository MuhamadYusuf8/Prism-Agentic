"""
Celery application configuration — PRISM recruitment system.

Configured tasks:
  - daily-linkedin-cs-scrape     : Runs daily at 8am WIB (86400s)
  - hourly-follow-up-dispatch    : Check & send follow-up emails every hour
  - daily-inbox-sync             : Sync IMAP inbox for replies every 2 hours
"""

from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "recruitment",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.scrape_tasks", "app.workers.email_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # ── Scraping ──────────────────────────────────────────────────────────
        # Scrape LinkedIn CS profiles once a day at 8am WIB
        "daily-linkedin-cs-scrape": {
            "task": "app.workers.scrape_tasks.run_linkedin_scrape",
            "schedule": 86400,  # 24 hours
            "kwargs": {"max_profiles": 50},
        },
        # ── Email Follow-ups ──────────────────────────────────────────────────
        # Check all active campaigns every 6 hours and send pending follow-ups
        "periodic-follow-up-dispatch": {
            "task": "app.workers.email_tasks.run_periodic_follow_ups",
            "schedule": 6 * 3600,  # every 6 hours
        },
    },
)
