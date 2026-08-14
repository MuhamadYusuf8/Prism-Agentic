from app.core.celery_app import celery_app


@celery_app.task(name="app.workers.email_tasks.send_bulk_outreach")
def send_bulk_outreach(lead_ids: list[str]):
    """Queue bulk email sending for a list of lead IDs."""
    # TODO: iterate leads, draft + send email per lead
    pass
