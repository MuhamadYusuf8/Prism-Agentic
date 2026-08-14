import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Core ────────────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    # ── Targeting ───────────────────────────────────────────────────────────────
    target_type: Mapped[str | None] = mapped_column(String(50))  # bachelor/master/all
    target_clusters: Mapped[list | None] = mapped_column(JSON)  # list of cluster IDs

    # ── Email Template ──────────────────────────────────────────────────────────
    email_template: Mapped[dict | None] = mapped_column(
        JSON,
        comment="""{
            subject: str,
            body: str (HTML),
            variables: [str] (e.g. {{name}}, {{program}}, etc.)
        }""",
    )

    # ── Follow-up Configuration ─────────────────────────────────────────────────
    follow_up: Mapped[dict | None] = mapped_column(
        JSON,
        comment="""{
            enabled: bool,
            delay_days: int,
            max_follow_ups: int,
            template: {subject, body}
        }""",
    )

    # ── Schedule ────────────────────────────────────────────────────────────────
    schedule: Mapped[dict | None] = mapped_column(
        JSON,
        comment="""{
            start_date: datetime,
            end_date: datetime,
            timezone: str,
            send_window: {start: str, end: str}
        }""",
    )

    # ── Stats ───────────────────────────────────────────────────────────────────
    stats: Mapped[dict | None] = mapped_column(
        JSON,
        default=dict,
        comment="""{
            total_targeted: int,
            emails_sent: int,
            emails_opened: int,
            emails_clicked: int,
            replies_received: int,
            interested: int,
            unsubscribed: int,
            bounced: int
        }""",
    )

    # ── Status ──────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default="draft", index=True
    )  # draft/active/paused/completed/cancelled
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    # ── Timestamps ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    launched_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
