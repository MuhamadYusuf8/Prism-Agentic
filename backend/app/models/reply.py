import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Boolean, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class Reply(Base):
    __tablename__ = "replies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Associations ────────────────────────────────────────────────────────────
    email_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    campaign_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # ── Reply Content ───────────────────────────────────────────────────────────
    from_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(512))
    body: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)  # plain text version

    # ── Intent Classification ───────────────────────────────────────────────────
    intent: Mapped[str | None] = mapped_column(
        String(50), index=True
    )  # interested/not_interested/request_info/unsubscribe/out_of_office/neutral/other
    confidence: Mapped[float | None] = mapped_column(Float)  # 0.0 - 1.0
    sentiment: Mapped[str | None] = mapped_column(String(20))  # positive/negative/neutral

    # ── Auto-Response ───────────────────────────────────────────────────────────
    auto_response_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_response_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    auto_response_body: Mapped[str | None] = mapped_column(Text)

    # ── Raw Data ────────────────────────────────────────────────────────────────
    raw_data: Mapped[dict | None] = mapped_column(JSON)

    # ── Timestamps ──────────────────────────────────────────────────────────────
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
