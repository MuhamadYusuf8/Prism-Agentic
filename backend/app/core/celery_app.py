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
    beat_schedule={
        # Scrape LinkedIn CS profiles every day at 8am WIB
        "daily-linkedin-cs-scrape": {
            "task": "app.workers.scrape_tasks.run_linkedin_scrape",
            "schedule": 86400,
            "kwargs": {"max_profiles": 50},
        },
    },
)
