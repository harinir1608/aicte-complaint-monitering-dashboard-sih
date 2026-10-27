from __future__ import annotations

import uuid
import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .bureau import Region
    from .user import User
    from .complaint import Complaint
    from .case import Case


class InstitutionType(str, enum.Enum):
    engineering = "engineering"
    pharmacy = "pharmacy"
    management = "management"
    polytechnic = "polytechnic"
    architecture = "architecture"
    other = "other"


class AliasType(str, enum.Enum):
    abbreviation = "abbreviation"
    former_name = "former_name"
    colloquial = "colloquial"
    other = "other"


class Institution(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "institutions"

    permanent_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    state: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("regions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    institution_type: Mapped[Optional[InstitutionType]] = mapped_column(
        Enum(InstitutionType, name="institution_type_enum"),
        nullable=True,
    )
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pin_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    region: Mapped[Optional["Region"]] = relationship("Region", back_populates="institutions")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    aliases: Mapped[List["InstitutionAlias"]] = relationship(
        "InstitutionAlias", back_populates="institution", cascade="all, delete-orphan"
    )
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="institution")
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="institution")

    def __repr__(self) -> str:
        return f"<Institution name={self.name!r} permanent_id={self.permanent_id!r}>"


class InstitutionAlias(UUIDMixin, Base):
    __tablename__ = "institution_aliases"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alias: Mapped[str] = mapped_column(String(500), nullable=False)
    alias_type: Mapped[AliasType] = mapped_column(
        Enum(AliasType, name="alias_type_enum"),
        nullable=False,
        default=AliasType.other,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    institution: Mapped["Institution"] = relationship("Institution", back_populates="aliases")

    def __repr__(self) -> str:
        return f"<InstitutionAlias alias={self.alias!r} type={self.alias_type!r}>"
