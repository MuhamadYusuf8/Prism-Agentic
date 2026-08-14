"""
Analytics routes — comprehensive stats ported from recruit-Z's analytics
and intake-agent-2's dashboard stats.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text

from app.core.database import get_db
from app.models.lead import Lead
from app.models.campaign import Campaign
from app.models.email_log import EmailLog
from app.models.reply import Reply
from app.models.cluster import Cluster
from app.services.profiling import get_profiling_stats
from app.services.clustering import get_cluster_stats
from app.services.reply_monitor import get_reply_stats

router = APIRouter()


@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)):
    """Comprehensive dashboard summary."""
    total = await db.scalar(select(func.count(Lead.id)))
    active = await db.scalar(
        select(func.count(Lead.id)).where(Lead.is_active == True)
    )

    # By status
    by_status = await db.execute(
        select(Lead.status, func.count(Lead.id)).group_by(Lead.status)
    )

    # By source
    by_source = await db.execute(
        select(Lead.source, func.count(Lead.id)).group_by(Lead.source)
    )

    # By profile type
    by_type = await db.execute(
        select(Lead.profile_type, func.count(Lead.id))
        .where(Lead.profile_type.isnot(None))
        .group_by(Lead.profile_type)
    )

    # By study field (computer_science | management | law)
    by_field = await db.execute(
        select(Lead.field, func.count(Lead.id))
        .where(Lead.field.isnot(None))
        .group_by(Lead.field)
    )

    # By data quality
    by_quality = await db.execute(
        select(Lead.data_quality, func.count(Lead.id))
        .where(Lead.data_quality.isnot(None))
        .group_by(Lead.data_quality)
    )

    # Averages
    avg_score = await db.scalar(select(func.avg(Lead.profile_score)))
    avg_priority = await db.scalar(select(func.avg(Lead.priority_score)))

    # CS related count
    cs_related = await db.scalar(
        select(func.count(Lead.id)).where(Lead.is_computer_science_related == True)
    )

    # Campaign stats
    active_campaigns = await db.scalar(
        select(func.count(Campaign.id)).where(Campaign.status == "active")
    )
    total_campaigns = await db.scalar(select(func.count(Campaign.id)))

    # Cluster stats
    total_clusters = await db.scalar(
        select(func.count(Cluster.id)).where(Cluster.is_active == True)
    )

    # Email stats
    total_sent = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.status == "sent")
    )
    total_opened = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.opened_at.isnot(None))
    )
    total_replied = await db.scalar(
        select(func.count(EmailLog.id)).where(EmailLog.replied_at.isnot(None))
    )

    return {
        "total_leads": total or 0,
        "active_leads": active or 0,
        "cs_related": cs_related or 0,
        "avg_profile_score": round(float(avg_score or 0), 2),
        "avg_priority_score": round(float(avg_priority or 0), 2),
        "by_status": {row[0]: row[1] for row in by_status},
        "by_source": {row[0]: row[1] for row in by_source},
        "by_profile_type": {row[0]: row[1] for row in by_type},
        "by_field": {row[0]: row[1] for row in by_field},
        "by_data_quality": {row[0]: row[1] for row in by_quality},
        "campaigns": {
            "total": total_campaigns or 0,
            "active": active_campaigns or 0,
        },
        "clusters": {
            "total": total_clusters or 0,
        },
        "email_stats": {
            "sent": total_sent or 0,
            "opened": total_opened or 0,
            "replied": total_replied or 0,
            "open_rate": round((total_opened or 0) / max(total_sent or 1, 1) * 100, 2),
        },
    }


@router.get("/funnel")
async def funnel(db: AsyncSession = Depends(get_db)):
    """Pipeline funnel — count leads at each stage."""
    stages = ["new", "scraped", "profiled", "clustered", "contacted",
              "interested", "applied", "enrolled", "not_interested", "unsubscribed"]
    result = {}
    for stage in stages:
        count = await db.scalar(
            select(func.count(Lead.id)).where(Lead.status == stage)
        )
        result[stage] = count or 0
    return result


@router.get("/trends")
async def trends(db: AsyncSession = Depends(get_db)):
    """Weekly lead creation trends (last 12 weeks)."""
    rows = await db.execute(
        text("""
            SELECT DATE_TRUNC('week', created_at) AS week, COUNT(*) AS count
            FROM leads
            WHERE created_at >= NOW() - INTERVAL '12 weeks'
            GROUP BY week ORDER BY week
        """)
    )
    return [{"week": str(r[0]), "count": r[1]} for r in rows]


@router.get("/by-education")
async def by_education(db: AsyncSession = Depends(get_db)):
    """Count leads by education level."""
    rows = await db.execute(
        select(Lead.education_level, func.count(Lead.id))
        .where(Lead.education_level.isnot(None))
        .group_by(Lead.education_level)
    )
    return {"by_level": {row[0]: row[1] for row in rows}}


@router.get("/by-program")
async def by_program(db: AsyncSession = Depends(get_db)):
    """Count leads by recommended program."""
    rows = await db.execute(
        select(Lead.recommended_program, func.count(Lead.id))
        .where(Lead.recommended_program.isnot(None))
        .group_by(Lead.recommended_program)
    )
    return [{"program": r[0], "count": r[1]} for r in rows]


@router.get("/profile-distribution")
async def profile_distribution(db: AsyncSession = Depends(get_db)):
    """Profile score distribution (buckets)."""
    buckets = [
        (0, 20), (20, 40), (40, 60), (60, 80), (80, 100)
    ]
    result = []
    for low, high in buckets:
        count = await db.scalar(
            select(func.count(Lead.id))
            .where(Lead.profile_score >= low)
            .where(Lead.profile_score < high)
        )
        result.append({"range": f"{low}-{high}", "count": count or 0})
    return result


@router.get("/top-prospects")
async def top_prospects(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Top scored leads."""
    result = await db.execute(
        select(Lead)
        .where(Lead.is_active == True)
        .order_by(Lead.profile_score.desc().nulls_last())
        .limit(limit)
    )
    leads = result.scalars().all()
    return {
        "data": [
            {
                "id": str(l.id),
                "name": l.name,
                "email": l.email,
                "profile_score": l.profile_score,
                "profile_type": l.profile_type,
                "status": l.status,
                "source": l.source,
                "field": l.field,
                "recommended_program": l.recommended_program,
            }
            for l in leads
        ]
    }
