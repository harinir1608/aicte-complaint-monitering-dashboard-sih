from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db

# ── Password hashing ──────────────────────────────────────────────────────────

_ph = PasswordHasher()


def hash_password(plain: str) -> str:
    """Return an argon2 hash of the given plain-text password."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the stored *hashed* password."""
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# ── JWT ───────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _make_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(
    *,
    user_id: uuid.UUID,
    email: str,
    role: str,
) -> str:
    """Create a short-lived access JWT."""
    return _make_token(
        {
            "sub": email,
            "user_id": str(user_id),
            "role": role,
            "type": "access",
        },
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(
    *,
    user_id: uuid.UUID,
    email: str,
) -> str:
    """Create a longer-lived refresh JWT."""
    return _make_token(
        {
            "sub": email,
            "user_id": str(user_id),
            "type": "refresh",
        },
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and return the JWT payload or raise HTTPException 401."""
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise credentials_exc


def verify_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """Verify a token and check its type claim."""
    payload = decode_token(token)
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected '{expected_type}'.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ── FastAPI dependencies ──────────────────────────────────────────────────────


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """Decode the access token and return the corresponding User object."""
    from app.models.user import User  # local import avoids circular deps

    payload = verify_token(token, expected_type="access")
    user_id_str: Optional[str] = payload.get("user_id")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user_id claim",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user_id in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user=Depends(get_current_user)):
    """Ensure the authenticated user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


# ── Role-based permission helpers ─────────────────────────────────────────────


def require_role(*roles: str):
    """Return a dependency that enforces one of the given roles."""

    def _check(current_user=Depends(get_current_active_user)):
        if current_user.role not in roles and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires one of these roles: {', '.join(roles)}",
            )
        return current_user

    return _check


def require_admin(current_user=Depends(get_current_active_user)):
    """Dependency: current user must be system_admin or superuser."""
    from app.models.user import UserRole

    if current_user.role != UserRole.system_admin and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
