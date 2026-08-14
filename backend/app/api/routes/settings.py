"""
Settings routes — ports from student-intake-agent Settings.js.

Provides CRUD for application settings stored in a simple JSON config
(Email SMTP, LinkedIn scraper, Email monitoring, General settings).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db

router = APIRouter()

# ── In-memory settings store (replace with DB table in production) ──────────

_settings_store: dict = {
    "email": {
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_pass": "",
        "from_name": "Admissions Team",
        "from_email": "",
    },
    "linkedin": {
        "email": "",
        "password": "",
        "max_requests": 50,
        "li_at": "",
    },
    "monitoring": {
        "check_interval_minutes": 5,
        "auto_follow_up": False,
        "notify_on_reply": True,
    },
    "general": {
        "institution_name": "President University",
        "program_url": "https://president.ac.id/programs",
        "reply_to_email": "",
    },
}


# ── Schemas ─────────────────────────────────────────────────────────────────


class EmailSettings(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_user: str | None = None
    smtp_pass: str | None = None
    from_name: str | None = None
    from_email: str | None = None


class LinkedInSettings(BaseModel):
    email: str | None = None
    password: str | None = None
    max_requests: int | None = None
    li_at: str | None = None


class MonitoringSettings(BaseModel):
    check_interval_minutes: int | None = None
    auto_follow_up: bool | None = None
    notify_on_reply: bool | None = None


class GeneralSettings(BaseModel):
    institution_name: str | None = None
    program_url: str | None = None
    reply_to_email: str | None = None


class SettingsUpdate(BaseModel):
    email: EmailSettings | None = None
    linkedin: LinkedInSettings | None = None
    monitoring: MonitoringSettings | None = None
    general: GeneralSettings | None = None


# ── Routes ──────────────────────────────────────────────────────────────────


@router.get("/settings")
async def get_settings():
    """Get all application settings."""
    return _settings_store


@router.put("/settings")
async def update_settings(payload: SettingsUpdate):
    """Update application settings."""
    global _settings_store

    if payload.email:
        _settings_store["email"].update(payload.email.model_dump(exclude_none=True))
    if payload.linkedin:
        _settings_store["linkedin"].update(payload.linkedin.model_dump(exclude_none=True))
    if payload.monitoring:
        _settings_store["monitoring"].update(payload.monitoring.model_dump(exclude_none=True))
    if payload.general:
        _settings_store["general"].update(payload.general.model_dump(exclude_none=True))

    return _settings_store


@router.get("/settings/{section}")
async def get_settings_section(section: str):
    """Get a specific settings section."""
    if section not in _settings_store:
        raise HTTPException(404, f"Settings section '{section}' not found")
    return _settings_store[section]


@router.put("/settings/{section}")
async def update_settings_section(section: str, payload: dict):
    """Update a specific settings section."""
    if section not in _settings_store:
        raise HTTPException(404, f"Settings section '{section}' not found")
    _settings_store[section].update(payload)
    return _settings_store[section]
