from __future__ import annotations

import uuid
import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bureau import Bureau, Region
    from .case import CaseAssignment, CaseAction


class UserRole(str, enum.Enum):
    system_admin = "system_admin"
    rb_officer = "rb_officer"
    pgrc_officer = "pgrc_officer"
    bureau_officer = "bureau_officer"
    regional_officer = "regional_officer"
    senior_management = "senior_management"


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    employee_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.bureau_officer,
    )
    bureau_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bureaus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    bureau: Mapped[Optional["Bureau"]] = relationship("Bureau", back_populates="users", foreign_keys=[bureau_id])
    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="users", foreign_keys=[region_id])

    def __repr__(self) -> str:
        return f"<User email={self.email!r} role={self.role!r}>"
