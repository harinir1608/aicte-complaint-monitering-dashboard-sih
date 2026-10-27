from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .institution import Institution
    from .complaint import Complaint
    from .case import Case
    from .notification import SLARule


class Bureau(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "bureaus"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="bureau", foreign_keys="User.bureau_id"
    )
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="bureau")
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="bureau")
    sla_rules: Mapped[List["SLARule"]] = relationship("SLARule", back_populates="bureau")

    def __repr__(self) -> str:
        return f"<Bureau code={self.code!r} name={self.name!r}>"


class Region(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "regions"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    states: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="region", foreign_keys="User.region_id"
    )
    institutions: Mapped[List["Institution"]] = relationship(
        "Institution", back_populates="region"
    )

    def __repr__(self) -> str:
        return f"<Region code={self.code!r} name={self.name!r}>"
