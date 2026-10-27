from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.auth import UserCreate


def get_user_by_email(email: str, db: Session) -> Optional[User]:
    """Return the User with the given email, or None."""
    return db.execute(select(User).where(User.email == email)).scalar_one_or_none()


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """Return User if credentials are valid, else None."""
    user = get_user_by_email(email, db)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def create_user(
    user_data: UserCreate,
    db: Session,
    created_by: Optional[User] = None,
) -> User:
    """
    Persist a new user and return the ORM instance.

    Raises ValueError if the email is already taken.
    """
    existing = get_user_by_email(user_data.email, db)
    if existing is not None:
        raise ValueError(f"Email already registered: {user_data.email}")

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        employee_id=user_data.employee_id,
        role=user_data.role,
        bureau_id=user_data.bureau_id,
        region_id=user_data.region_id,
        is_superuser=user_data.is_superuser,
        is_active=True,
    )
    db.add(user)
    db.flush()  # get the generated UUID without committing
    return user
