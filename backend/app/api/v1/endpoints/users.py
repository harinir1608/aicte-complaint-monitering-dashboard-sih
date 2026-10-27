from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, hash_password, require_admin
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserResponse, UserUpdate
from app.services.auth_service import create_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
def list_users(
    role: Optional[UserRole] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users with optional filters. Admin only."""
    stmt = select(User)
    if role is not None:
        stmt = stmt.where(User.role == role)
    if bureau_id is not None:
        stmt = stmt.where(User.bureau_id == bureau_id)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    stmt = stmt.offset(skip).limit(limit)
    users = db.execute(stmt).scalars().all()
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_new_user(
    user_data: UserCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new user. Admin only."""
    try:
        user = create_user(user_data, db, created_by=admin)
        db.commit()
        db.refresh(user)
        return user
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get user by ID. Admin can fetch any user; others can only fetch themselves."""
    from app.models.user import UserRole as UR

    if current_user.id != user_id and current_user.role != UR.system_admin and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    updates: UserUpdate,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user fields. Admin only."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_200_OK)
def deactivate_user(
    user_id: uuid.UUID,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Deactivate a user (set is_active=False). Admin only."""
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    db.commit()
    return {"detail": f"User {user.email} deactivated"}


@router.post("/{user_id}/reset-password", status_code=status.HTTP_200_OK)
def reset_user_password(
    user_id: uuid.UUID,
    new_password_data: dict,
    _: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Admin-controlled password reset."""
    new_password = new_password_data.get("new_password", "")
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.hashed_password = hash_password(new_password)
    db.commit()
    return {"detail": "Password reset successfully"}
