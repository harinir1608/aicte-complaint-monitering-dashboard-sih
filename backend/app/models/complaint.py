from __future__ import annotations

import uuid
import enum
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .bureau import Bureau
    from .institution import Institution
    from .case import Case


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ComplaintSource(str, enum.Enum):
    email = "email"
    portal = "portal"
    letter = "letter"
    phone = "phone"
    walk_in = "walk_in"
    ministry_reference = "ministry_reference"
    court = "court"
    rti = "rti"
    other = "other"


class ComplaintStatus(str, enum.Enum):
    received = "received"
    pending_assignment = "pending_assignment"
    under_process = "under_process"
    awaiting_information = "awaiting_information"
    transferred = "transferred"
    escalated = "escalated"
    disposed = "disposed"
    closed = "closed"


class ComplaintPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"
    critical = "critical"


class ComplaintCategory(UUIDMixin, Base):
    __tablename__ = "complaint_categories"

    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_sla_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="category")
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="category")

    def __repr__(self) -> str:
        return f"<ComplaintCategory code={self.code!r} name={self.name!r}>"


class Complaint(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "complaints"

    complaint_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    institution_name_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[ComplaintSource] = mapped_column(
        Enum(ComplaintSource, name="complaint_source_enum"),
        nullable=False,
        default=ComplaintSource.other,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaint_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    received_date: Mapped[date] = mapped_column(Date, nullable=False)
    complainant_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    complainant_contact: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    bureau_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bureaus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status_enum"),
        nullable=False,
        default=ComplaintStatus.received,
    )
    priority: Mapped[ComplaintPriority] = mapped_column(
        Enum(ComplaintPriority, name="complaint_priority_enum"),
        nullable=False,
        default=ComplaintPriority.normal,
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    institution: Mapped[Optional["Institution"]] = relationship(
        "Institution", back_populates="complaints"
    )
    category: Mapped[Optional["ComplaintCategory"]] = relationship(
        "ComplaintCategory", back_populates="complaints"
    )
    bureau: Mapped[Optional["Bureau"]] = relationship("Bureau", back_populates="complaints")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    documents: Mapped[List["ComplaintDocument"]] = relationship(
        "ComplaintDocument", back_populates="complaint", cascade="all, delete-orphan"
    )
    cases: Mapped[List["Case"]] = relationship("Case", back_populates="complaint")

    def __repr__(self) -> str:
        return f"<Complaint complaint_number={self.complaint_number!r}>"


class ComplaintDocument(UUIDMixin, Base):
    __tablename__ = "complaint_documents"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_key: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    uploaded_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="documents")
    uploaded_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[uploaded_by_id])
