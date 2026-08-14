import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Core ────────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # bachelor/master/phd/professional/mixed

    # ── Characteristics ─────────────────────────────────────────────────────────
    characteristics: Mapped[dict | None] = mapped_column(
        JSON,
        comment="""{
            average_score: float,
            common_skills: [str],
            common_interests: [str],
            common_education_fields: [str],
            average_experience: float,
            top_locations: [{name: str, count: int}]
        }""",
    )
    centroid: Mapped[list | None] = mapped_column(JSON)  # vector centroid for similarity
    member_count: Mapped[int] = mapped_column(Integer, default=0)

    # ── Campaign Association ────────────────────────────────────────────────────
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # ── Status ──────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Timestamps ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
