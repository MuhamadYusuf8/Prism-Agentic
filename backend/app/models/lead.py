import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, JSON, Enum as SAEnum, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
import enum

from app.core.database import Base


class LeadSource(str, enum.Enum):
    LINKEDIN_SERPER = "linkedin_serper"
    LINKEDIN_PUPPETEER = "linkedin_puppeteer"
    CSV_IMPORT = "csv_import"
    CIKARANG = "cikarang"
    MANUAL = "manual"
    API = "api"


class LeadStatus(str, enum.Enum):
    NEW = "new"
    SCRAPED = "scraped"
    PROFILED = "profiled"
    CLUSTERED = "clustered"
    CONTACTED = "contacted"
    INTERESTED = "interested"
    NOT_INTERESTED = "not_interested"
    APPLIED = "applied"
    ENROLLED = "enrolled"
    UNSUBSCRIBED = "unsubscribed"


class ProfileType(str, enum.Enum):
    MASTER = "master"
    PHD = "phd"
    PROFESSIONAL = "professional"
    UNKNOWN = "unknown"


class DataQuality(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index(
            "ux_leads_linkedin_url",
            "linkedin_url",
            unique=True,
            postgresql_where=text("linkedin_url IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ── Core Identity ───────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50))
    linkedin_url: Mapped[str | None] = mapped_column(String(512))

    # ── LinkedIn / Professional Data ────────────────────────────────────────────
    headline: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(String(255))
    job_title: Mapped[str | None] = mapped_column(String(255))
    industry: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    skills: Mapped[list | None] = mapped_column(JSON)  # list of skill strings
    education_level: Mapped[str | None] = mapped_column(String(100))  # SMA, D3, S1, S2, S3
    education: Mapped[list | None] = mapped_column(JSON)  # list of education entries
    experience: Mapped[list | None] = mapped_column(JSON)  # list of experience entries

    # ── Source & Status ────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default=LeadStatus.NEW.value, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # ── Study Field (computer_science | management | law) ─────────────────────
    field: Mapped[str | None] = mapped_column(String(50), index=True)

    # ── Profiling / Scoring ─────────────────────────────────────────────────────
    profile_score: Mapped[float | None] = mapped_column(Float)  # CS relevance 0-100
    profile_type: Mapped[str | None] = mapped_column(String(50))  # bachelor/master/phd/professional
    priority_score: Mapped[int | None] = mapped_column(Integer)
    is_computer_science_related: Mapped[bool | None] = mapped_column(Boolean)
    matched_programs: Mapped[list | None] = mapped_column(JSON)  # [{name, confidence, type}]
    recommended_program: Mapped[str | None] = mapped_column(String(255))
    tags: Mapped[list | None] = mapped_column(JSON)  # auto-generated tags
    data_quality: Mapped[str | None] = mapped_column(String(20))  # high/medium/low

    # ── Syllabus Matching (from dataset/Syllabus.txt) ──────────────────────────
    syllabus_confidence: Mapped[float | None] = mapped_column(Float)  # 0-100 overall
    syllabus_scores: Mapped[dict | None] = mapped_column(JSON)  # {subject: score, ...}
    syllabus_matched_subjects: Mapped[list | None] = mapped_column(JSON)  # ["ML", ...]
    syllabus_top_match: Mapped[str | None] = mapped_column(String(255))  # best subject

    # ── Clustering ──────────────────────────────────────────────────────────────
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)

    # ── Communication Tracking ──────────────────────────────────────────────────
    communication: Mapped[dict | None] = mapped_column(
        JSON,
        default=dict,
        comment="""{
            emails_sent: [{campaign_id, subject, sent_at, opened, opened_at, clicked, clicked_at, replied, replied_at}],
            interested: bool,
            interested_at: datetime,
            last_contacted_at: datetime
        }""",
    )

    # ── AI / Embeddings ─────────────────────────────────────────────────────────
    profile_embedding: Mapped[list | None] = mapped_column(JSON)

    # ── Raw Data & Notes ────────────────────────────────────────────────────────
    raw_data: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(Text)

    # ── Timestamps ──────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    profiled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_contacted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
