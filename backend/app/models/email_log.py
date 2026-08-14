import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Associations ────────────────────────────────────────────────────────────
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # ── Email Content ───────────────────────────────────────────────────────────
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    recipient_name: Mapped[str | None] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(512), nullable=False)
    body: Mapped[str | None] = mapped_column(Text)
    tracking_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)

    # ── Delivery Status ─────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(50), default="pending", index=True
    )  # pending/sent/delivered/bounced/failed
    error_message: Mapped[str | None] = mapped_column(Text)

    # ── Tracking ────────────────────────────────────────────────────────────────
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_count: Mapped[int] = mapped_column(default=0)
    clicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    clicked_count: Mapped[int] = mapped_column(default=0)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # ── Extra Data ──────────────────────────────────────────────────────────────
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)
    follow_up_number: Mapped[int | None] = mapped_column(default=0)
    extra_data: Mapped[dict | None] = mapped_column(JSON)

    # ── Timestamps ──────────────────────────────────────────────────────────────
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
