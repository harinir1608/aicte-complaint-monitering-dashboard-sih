from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    hash_password,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    Token,
    UserResponse,
)
from app.services.auth_service import authenticate_user, get_user_by_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Validate credentials and return JWT access + refresh tokens."""
    user = authenticate_user(payload.email, payload.password, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Update last_login
    user.last_login = datetime.now(timezone.utc)
    db.commit()

    return Token(
        access_token=create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        ),
        refresh_token=create_refresh_token(
            user_id=user.id,
            email=user.email,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a new access + refresh pair."""
    token_data = verify_token(payload.refresh_token, expected_type="refresh")
    user = get_user_by_email(token_data["sub"], db)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return Token(
        access_token=create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role,
        ),
        refresh_token=create_refresh_token(
            user_id=user.id,
            email=user.email,
        ),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(_: User = Depends(get_current_active_user)):
    """
    Stateless logout — the client should discard its tokens.
    A token blacklist can be added here if needed.
    """
    return {"detail": "Successfully logged out"}


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Allow the authenticated user to change their own password."""
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password changed successfully"}
