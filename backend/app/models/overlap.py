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
    from .case import Case


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MatchType(str, enum.Enum):
    exact_id = "exact_id"
    exact_reference = "exact_reference"
    institution_name_fuzzy = "institution_name_fuzzy"
    institution_name_semantic = "institution_name_semantic"
    complaint_similarity = "complaint_similarity"
    combined = "combined"


class OverlapAlertStatus(str, enum.Enum):
    pending_review = "pending_review"
    confirmed_related = "confirmed_related"
    false_positive = "false_positive"
    linked = "linked"
    dismissed = "dismissed"


class OverlapReviewDecision(str, enum.Enum):
    confirmed_related = "confirmed_related"
    false_positive = "false_positive"
    linked = "linked"
    maintain_separate = "maintain_separate"
    needs_investigation = "needs_investigation"


class OverlapAlert(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "overlap_alerts"

    alert_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    case_id_incoming: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    case_id_existing: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType, name="match_type_enum"),
        nullable=False,
    )
    match_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    match_evidence: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    bureaus_involved: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    # Explainability fields
    match_reasons: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    detection_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    status: Mapped[OverlapAlertStatus] = mapped_column(
        Enum(OverlapAlertStatus, name="overlap_alert_status_enum"),
        nullable=False,
        default=OverlapAlertStatus.pending_review,
    )

    # Relationships
    case_incoming: Mapped["Case"] = relationship("Case", foreign_keys=[case_id_incoming])
    case_existing: Mapped["Case"] = relationship("Case", foreign_keys=[case_id_existing])
    institution: Mapped[Optional["Institution"]] = relationship("Institution")
    reviews: Mapped[List["OverlapReview"]] = relationship(
        "OverlapReview", back_populates="alert", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<OverlapAlert alert_number={self.alert_number!r} status={self.status!r}>"


class OverlapReview(UUIDMixin, Base):
    __tablename__ = "overlap_reviews"

    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("overlap_alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewed_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    decision: Mapped[OverlapReviewDecision] = mapped_column(
        Enum(OverlapReviewDecision, name="overlap_review_decision_enum"),
        nullable=False,
    )
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coordination_owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    alert: Mapped["OverlapAlert"] = relationship("OverlapAlert", back_populates="reviews")
    reviewed_by: Mapped[Optional["User"]] = relationship("User", foreign_keys=[reviewed_by_id])
    coordination_owner: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[coordination_owner_id]
    )
