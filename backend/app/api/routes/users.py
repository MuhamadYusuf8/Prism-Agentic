from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, EmailStr
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.auth import get_current_user, require_admin, hash_password
from app.models.user import User
from app.models.audit_log import AuditLog

router = APIRouter()


class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str = "user"


class UserUpdate(BaseModel):
    role: str | None = None
    is_active: bool | None = None


class PasswordUpdate(BaseModel):
    new_password: str


async def log_audit(db: AsyncSession, user_id: UUID, action: str, resource_type: str, resource_id: str, details: dict, ip_address: str | None = None):
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


@router.get("/")
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    """List all users (Admin only)"""
    result = await db.execute(select(User).order_by(desc(User.created_at)))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "name": u.name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.post("/")
async def create_user(
    payload: UserCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new user (Admin only)"""
    # Check existing
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await log_audit(
        db=db,
        user_id=current_user.id,
        action="create_user",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": user.role},
        ip_address=request.client.host if request.client else None,
    )

    return {"id": str(user.id), "email": user.email, "name": user.name, "role": user.role}


@router.patch("/{user_id}")
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update user role or status (Admin only)"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if str(user.id) == str(current_user.id) and payload.is_active is False:
        raise HTTPException(400, "Cannot deactivate your own account")

    old_role = user.role
    old_active = user.is_active

    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    await db.commit()

    await log_audit(
        db=db,
        user_id=current_user.id,
        action="update_user",
        resource_type="user",
        resource_id=str(user.id),
        details={"old_role": old_role, "new_role": user.role, "old_active": old_active, "new_active": user.is_active},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True}


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete a user (Admin only)"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    
    if str(user.id) == str(current_user.id):
        raise HTTPException(400, "Cannot delete your own account")

    await db.delete(user)
    await db.commit()

    await log_audit(
        db=db,
        user_id=current_user.id,
        action="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        details={"email": user.email},
        ip_address=request.client.host if request.client else None,
    )


@router.get("/me")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }


@router.patch("/me/password")
async def update_my_password(
    payload: PasswordUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's password"""
    current_user.hashed_password = hash_password(payload.new_password)
    await db.commit()

    await log_audit(
        db=db,
        user_id=current_user.id,
        action="update_password",
        resource_type="user",
        resource_id=str(current_user.id),
        details={},
        ip_address=request.client.host if request.client else None,
    )

    return {"success": True}
