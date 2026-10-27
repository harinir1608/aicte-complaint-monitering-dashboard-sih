from __future__ import annotations

import uuid
import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from .user import User
    from .bureau import Bureau
    from .complaint import ComplaintCategory


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NotificationType(str, enum.Enum):
    assignment = "assignment"
    deadline_approaching = "deadline_approaching"
    overdue = "overdue"
    overlap_alert = "overlap_alert"
    transfer = "transfer"
    escalation = "escalation"
    system = "system"


class Notification(UUIDMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, name="notification_type_enum"),
        nullable=False,
        default=NotificationType.system,
    )
    related_entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])

    def __repr__(self) -> str:
        return f"<Notification user_id={self.user_id!r} type={self.notification_type!r}>"


class SLARule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sla_rules"

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
    priority: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sla_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    warning_days: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    escalation_days: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    bureau: Mapped[Optional["Bureau"]] = relationship("Bureau", back_populates="sla_rules")
    category: Mapped[Optional["ComplaintCategory"]] = relationship("ComplaintCategory")

    def __repr__(self) -> str:
        return f"<SLARule sla_days={self.sla_days!r} priority={self.priority!r}>"
