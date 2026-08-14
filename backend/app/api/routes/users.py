from uuid import UUID
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, hash_password
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter()

# ── Schemas ────────────────────────────────────────────────────────────────────

VALID_ROLES = {"admin", "recruiter", "viewer"}


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "viewer"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Role tidak valid. Pilihan: {VALID_ROLES}")
        return v


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str | None) -> str | None:
        if v is not None and v not in VALID_ROLES:
            raise ValueError(f"Role tidak valid. Pilihan: {VALID_ROLES}")
        return v


class PasswordUpdate(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password minimal 8 karakter")
        return v


# ── Internal Helpers ───────────────────────────────────────────────────────────


def _user_to_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "name": u.name,
        "role": u.role,
        "is_active": u.is_active,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login": u.last_login_at.isoformat() if u.last_login_at else None,  # ✅ correct field
    }


async def _log_audit(
    db: AsyncSession,
    user_id: UUID,
    action: str,
    resource_type: str,
    resource_id: str,
    details: dict,
    ip_address: str | None = None,
) -> None:
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(audit)
    await db.commit()


# ── Routes ─────────────────────────────────────────────────────────────────────
# IMPORTANT: /me and /me/password MUST come before /{user_id} to avoid route conflict


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return _user_to_dict(current_user)


@router.patch("/me/password")
async def update_my_password(
    payload: PasswordUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's own password."""
    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    await _log_audit(
        db=db,
        user_id=current_user.id,
        action="update_password",
        resource_type="user",
        resource_id=str(current_user.id),
        details={},
        ip_address=request.client.host if request.client else None,
    )
    return {"success": True}


@router.get("/")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all users with pagination (Admin only)."""
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count()).select_from(User))
    total = total_result.scalar_one()

    result = await db.execute(
        select(User).order_by(desc(User.created_at)).offset(offset).limit(page_size)
    )
    users = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [_user_to_dict(u) for u in users],
    }


@router.post("/", status_code=201)
async def create_user(
    payload: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user (Admin only)."""
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(409, "Email sudah terdaftar")

    user = User(
        email=payload.email,
        name=payload.name,
        password_hash=hash_password(payload.password),  # ✅ correct field name
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await _log_audit(
        db=db,
        user_id=current_user.id,
        action="create_user",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role},
        ip_address=request.client.host if request.client else None,
    )

    return _user_to_dict(user)


@router.get("/audit-logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Get audit log trail (Admin only)."""
    offset = (page - 1) * page_size

    total_result = await db.execute(select(func.count()).select_from(AuditLog))
    total = total_result.scalar_one()

    result = await db.execute(
        select(AuditLog, User.name, User.email)
        .outerjoin(User, User.id == AuditLog.user_id)
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [
            {
                "id": str(row.AuditLog.id),
                "action": row.AuditLog.action,
                "resource_type": row.AuditLog.resource_type,
                "resource_id": row.AuditLog.resource_id,
                "details": row.AuditLog.details,
                "ip_address": row.AuditLog.ip_address,
                "created_at": row.AuditLog.created_at.isoformat() if row.AuditLog.created_at else None,
                "actor_name": row.name,
                "actor_email": row.email,
            }
            for row in rows
        ],
    }


@router.patch("/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user role or active status (Admin only)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Pengguna tidak ditemukan")

    if str(user.id) == str(current_user.id) and payload.is_active is False:
        raise HTTPException(400, "Tidak bisa menonaktifkan akun sendiri")

    old_role = user.role
    old_active = user.is_active

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()

    await _log_audit(
        db=db,
        user_id=current_user.id,
        action="update_user",
        resource_type="user",
        resource_id=str(user.id),
        details={
            "old_role": old_role,
            "new_role": user.role,
            "old_active": old_active,
            "new_active": user.is_active,
        },
        ip_address=request.client.host if request.client else None,
    )

    return _user_to_dict(user)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user permanently (Admin only)."""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Pengguna tidak ditemukan")

    if str(user.id) == str(current_user.id):
        raise HTTPException(400, "Tidak bisa menghapus akun sendiri")

    email_snapshot = user.email
    await db.delete(user)
    await db.commit()

    await _log_audit(
        db=db,
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": email_snapshot},
        ip_address=request.client.host if request.client else None,
    )
