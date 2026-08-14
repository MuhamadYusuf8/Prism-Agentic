"""
Startup bootstrap — ensures the database is in a usable state whenever the
backend boots, so a fresh deployment works out of the box without requiring a
manual seed step.

Currently guarantees the default admin account exists (idempotent), so the
login page is usable immediately after `docker compose up`.
"""

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.auth import hash_password
from app.models.user import User

logger = logging.getLogger("prism.bootstrap")


async def ensure_default_admin() -> None:
    """Idempotently create the default admin account if it doesn't exist."""
    async with AsyncSessionLocal() as db:
        existing = await db.scalar(select(User).where(User.email == settings.ADMIN_EMAIL))
        if existing is not None:
            logger.info("admin already exists: %s", settings.ADMIN_EMAIL)
            return

        admin = User(
            name="Admin PRISM",
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        logger.info("created default admin account: %s", settings.ADMIN_EMAIL)
