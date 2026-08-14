"""
Clustering Service — ports from student-intake-agent-2 clusteringService.js.

Groups leads into clusters based on profile type (master)
and updates cluster characteristics.
"""

import uuid
from datetime import datetime, timezone
from typing import Any
from collections import Counter

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead import Lead, ProfileType
from app.models.cluster import Cluster


# ── Cluster Templates ──────────────────────────────────────────────────────────

CLUSTER_TEMPLATES = {
    ProfileType.MASTER.value: {
        "name": "Master Candidates",
        "description": "Prospective graduate students with master-level profiles",
        "type": ProfileType.MASTER.value,
        "characteristics": {
            "average_score": 0,
            "common_skills": [],
            "common_interests": [],
            "common_education_fields": [],
            "average_experience": 0,
            "top_locations": [],
        },
    },
}


def _calculate_total_experience(lead: Lead) -> float:
    """Calculate total years of experience from the lead's experience entries."""
    if not lead.experience:
        return 0

    total_years = 0.0
    for exp in lead.experience:
        if isinstance(exp, dict):
            # Try to parse duration from experience entry
            duration = exp.get("duration") or exp.get("years") or ""
            if duration:
                try:
                    total_years += float(duration)
                except (ValueError, TypeError):
                    total_years += 1  # default 1 year if unparseable
            else:
                total_years += 1  # default 1 year per entry
    return total_years


def _get_top_locations(locations: list[str | None], top_n: int = 5) -> list[dict]:
    """Get top N locations with counts."""
    valid = [loc for loc in locations if loc]
    if not valid:
        return []
    counter = Counter(valid)
    return [
        {"name": name, "count": count}
        for name, count in counter.most_common(top_n)
    ]


def _update_cluster_characteristics(cluster: Cluster, members: list[Lead]) -> Cluster:
    """Update cluster characteristics based on member data."""
    if not members:
        return cluster

    scores = [m.profile_score or 0 for m in members]
    all_skills = []
    all_interests = []
    all_education_fields = []
    all_locations = []

    for member in members:
        if member.skills:
            all_skills.extend(member.skills)
        if member.tags:
            # Extract interest tags
            interest_tags = [t for t in member.tags if t.startswith("interest_")]
            all_interests.extend(interest_tags)
        if member.education:
            for edu in member.education:
                if isinstance(edu, dict):
                    field = edu.get("field") or edu.get("degree") or edu.get("major")
                    if field:
                        all_education_fields.append(field)
        all_locations.append(member.location)

    cluster.characteristics = {
        "average_score": round(sum(scores) / len(scores), 2) if scores else 0,
        "common_skills": list(set(all_skills))[:20],
        "common_interests": list(set(all_interests))[:10],
        "common_education_fields": list(set(all_education_fields))[:10],
        "average_experience": round(
            sum(_calculate_total_experience(m) for m in members) / len(members), 1
        ) if members else 0,
        "top_locations": _get_top_locations(all_locations),
    }
    cluster.member_count = len(members)

    return cluster


async def determine_cluster(lead: Lead) -> str:
    """
    Determine which cluster type a lead belongs to based on profile type.
    """
    if lead.profile_type and lead.profile_type in CLUSTER_TEMPLATES:
        return lead.profile_type
    return ProfileType.UNKNOWN.value


async def cluster_leads(db: AsyncSession, lead_ids: list[uuid.UUID] | None = None) -> dict:
    """
    Cluster leads by profile type. Creates or updates clusters in the database.
    """
    # Get leads to cluster
    query = select(Lead).where(
        Lead.profile_type.isnot(None),
        Lead.profile_type != ProfileType.UNKNOWN.value,
        Lead.is_active == True,
    )
    if lead_ids:
        query = query.where(Lead.id.in_(lead_ids))

    result = await db.execute(query)
    leads = result.scalars().all()

    # Group leads by profile type
    grouped: dict[str, list[Lead]] = {}
    for lead in leads:
        cluster_type = lead.profile_type or ProfileType.UNKNOWN.value
        if cluster_type not in grouped:
            grouped[cluster_type] = []
        grouped[cluster_type].append(lead)

    # Create or update clusters
    clusters_created = 0
    clusters_updated = 0

    for cluster_type, members in grouped.items():
        template = CLUSTER_TEMPLATES.get(cluster_type)
        if not template:
            continue

        # Check if cluster already exists for this type
        existing = await db.execute(
            select(Cluster).where(
                Cluster.type == cluster_type,
                Cluster.is_active == True,
            )
        )
        cluster = existing.scalar_one_or_none()

        if not cluster:
            cluster = Cluster(
                name=template["name"],
                description=template["description"],
                type=template["type"],
                characteristics=template["characteristics"],
                member_count=0,
                is_active=True,
            )
            db.add(cluster)
            clusters_created += 1
        else:
            clusters_updated += 1

        # Update characteristics
        cluster = _update_cluster_characteristics(cluster, members)

        # Assign leads to this cluster
        for member in members:
            member.cluster_id = cluster.id
            if member.status in ("profiled", "new", "scraped"):
                from app.models.lead import LeadStatus
                member.status = LeadStatus.CLUSTERED.value

    await db.commit()

    return {
        "total_leads_processed": len(leads),
        "clusters_created": clusters_created,
        "clusters_updated": clusters_updated,
        "clusters": list(grouped.keys()),
    }


async def get_cluster_stats(db: AsyncSession) -> dict:
    """Get aggregate cluster statistics."""
    result = await db.execute(
        select(Cluster).where(Cluster.is_active == True).order_by(Cluster.member_count.desc())
    )
    clusters = result.scalars().all()

    return {
        "total_clusters": len(clusters),
        "clusters": [
            {
                "id": str(c.id),
                "name": c.name,
                "type": c.type,
                "member_count": c.member_count,
                "characteristics": c.characteristics,
            }
            for c in clusters
        ],
    }
