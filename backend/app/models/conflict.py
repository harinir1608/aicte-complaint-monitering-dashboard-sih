from __future__ import annotations

import uuid
import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .institution import Institution


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConflictSeverity(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ConflictStatus(str, enum.Enum):
    open = "open"
    acknowledged = "acknowledged"
    resolved = "resolved"
    dismissed = "dismissed"


class ConflictAlert(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "conflict_alerts"

    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    case_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    bureau_ids: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    rule_triggered: Mapped[str] = mapped_column(String(200), nullable=False)
    rule_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    severity: Mapped[ConflictSeverity] = mapped_column(
        Enum(ConflictSeverity, name="conflict_severity_enum"),
        nullable=False,
        default=ConflictSeverity.medium,
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coordination_owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[ConflictStatus] = mapped_column(
        Enum(ConflictStatus, name="conflict_status_enum"),
        nullable=False,
        default=ConflictStatus.open,
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    institution: Mapped[Optional["Institution"]] = relationship("Institution")
    coordination_owner: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[coordination_owner_id]
    )
    resolved_by: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[resolved_by_id]
    )

    def __repr__(self) -> str:
        return f"<ConflictAlert rule={self.rule_triggered!r} severity={self.severity!r}>"
