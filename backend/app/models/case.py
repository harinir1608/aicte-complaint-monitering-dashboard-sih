from __future__ import annotations

import uuid
import enum
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .bureau import Bureau
    from .institution import Institution
    from .complaint import Complaint, ComplaintCategory


class CaseStatus(str, enum.Enum):
    received = "received"
    pending_assignment = "pending_assignment"
    under_process = "under_process"
    awaiting_information = "awaiting_information"
    transferred = "transferred"
    escalated = "escalated"
    disposed = "disposed"
    closed = "closed"


class CasePriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"
    critical = "critical"


class CaseActionType(str, enum.Enum):
    note = "note"
    status_change = "status_change"
    assignment = "assignment"
    transfer = "transfer"
    escalation = "escalation"
    document_upload = "document_upload"
    decision = "decision"
    reminder = "reminder"
    other = "other"


class RelationshipType(str, enum.Enum):
    same_institution = "same_institution"
    same_complaint = "same_complaint"
    similar_issue = "similar_issue"
    escalation = "escalation"
    transfer = "transfer"
    other = "other"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Case(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cases"

    case_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    complaint_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    bureau_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bureaus.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaint_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CaseStatus] = mapped_column(
        Enum(CaseStatus, name="case_status_enum"),
        nullable=False,
        default=CaseStatus.received,
    )
    priority: Mapped[CasePriority] = mapped_column(
        Enum(CasePriority, name="case_priority_enum"),
        nullable=False,
        default=CasePriority.normal,
    )
    sla_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_disposal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    disposal_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    disposal_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", back_populates="cases")
    institution: Mapped[Optional["Institution"]] = relationship("Institution", back_populates="cases")
    bureau: Mapped[Optional["Bureau"]] = relationship("Bureau", back_populates="cases")
    category: Mapped[Optional["ComplaintCategory"]] = relationship("ComplaintCategory", back_populates="cases")
    created_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[created_by_id])
    assignments: Mapped[List["CaseAssignment"]] = relationship(
        "CaseAssignment", back_populates="case", cascade="all, delete-orphan"
    )
    actions: Mapped[List["CaseAction"]] = relationship(
        "CaseAction", back_populates="case", cascade="all, delete-orphan"
    )
    documents: Mapped[List["CaseDocument"]] = relationship(
        "CaseDocument", back_populates="case", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Case case_number={self.case_number!r}>"


class CaseAssignment(UUIDMixin, Base):
    __tablename__ = "case_assignments"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assigned_to_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="assignments")
    assigned_to: Mapped["User"] = relationship("User", foreign_keys=[assigned_to_id])
    assigned_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[assigned_by_id])


class CaseAction(UUIDMixin, Base):
    __tablename__ = "case_actions"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[CaseActionType] = mapped_column(
        Enum(CaseActionType, name="case_action_type_enum"),
        nullable=False,
        default=CaseActionType.note,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    old_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)

    # Relationships
    case: Mapped["Case"] = relationship("Case", back_populates="actions")
    performed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[performed_by_id])


class CaseDocument(UUIDMixin, Base):
    __tablename__ = "case_documents"

    case_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
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
    case: Mapped["Case"] = relationship("Case", back_populates="documents")
    uploaded_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[uploaded_by_id])


class RelatedCase(UUIDMixin, Base):
    __tablename__ = "related_cases"

    case_id_1: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id_2: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relationship_type: Mapped[RelationshipType] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum"),
        nullable=False,
        default=RelationshipType.other,
    )
    rationale: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linked_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    coordination_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    case1: Mapped["Case"] = relationship("Case", foreign_keys=[case_id_1])
    case2: Mapped["Case"] = relationship("Case", foreign_keys=[case_id_2])
    linked_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[linked_by_id])
