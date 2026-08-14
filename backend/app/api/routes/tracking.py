"""
Email tracking routes — open tracking pixel and click tracking redirects.

Ported from student-intake-agent-2 and student-recruitment-automation_duplicateZ.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.email_log import EmailLog

router = APIRouter(tags=["tracking"])


@router.get("/tracking/open/{tracking_id}")
async def track_open(
    tracking_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Tracking pixel endpoint — logs when an email is opened.
    Returns a 1x1 transparent GIF.
    """
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()

    if email_log:
        if not email_log.opened_at:
            email_log.opened_at = datetime.now(timezone.utc)
        email_log.opened_count = (email_log.opened_count or 0) + 1
        await db.commit()

    # Return 1x1 transparent GIF
    return Response(
        content=(
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00"
            b"\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00"
            b"\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00"
            b"\x00\x02\x02\x44\x01\x00\x3b"
        ),
        media_type="image/gif",
    )


@router.get("/tracking/click/{tracking_id}")
async def track_click(
    tracking_id: str,
    url: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    Click tracking endpoint — logs when a link is clicked, then redirects.
    """
    result = await db.execute(
        select(EmailLog).where(EmailLog.tracking_id == tracking_id)
    )
    email_log = result.scalar_one_or_none()

    if email_log:
        if not email_log.clicked_at:
            email_log.clicked_at = datetime.now(timezone.utc)
        email_log.clicked_count = (email_log.clicked_count or 0) + 1
        await db.commit()

    # Redirect to the original URL
    return RedirectResponse(url=url)
