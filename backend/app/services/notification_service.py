"""
Notification service — creates, queries, and marks Notification records.
"""
from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType
from app.models.case import Case
from app.models.overlap import OverlapAlert
from app.models.bureau import Bureau

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Simple pagination helper
# ---------------------------------------------------------------------------

class PaginatedResponse:
    def __init__(self, items, total: int, page: int, page_size: int):
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = (total + page_size - 1) // page_size if page_size > 0 else 0


class NotificationService:
    """CRUD and business-logic wrapper for Notification records."""

    # ------------------------------------------------------------------
    # Create helpers
    # ------------------------------------------------------------------

    def create_notification(
        self,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: NotificationType,
        entity_type: Optional[str],
        entity_id: Optional[uuid.UUID],
        db: Session,
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            related_entity_type=entity_type,
            related_entity_id=entity_id,
            is_read=False,
        )
        db.add(notif)
        db.flush()
        return notif

    def notify_assignment(
        self,
        case: Case,
        assigned_to_id: uuid.UUID,
        db: Session,
    ) -> Notification:
        return self.create_notification(
            user_id=assigned_to_id,
            title="New Case Assigned",
            message=(
                f"Case {case.case_number} has been assigned to you. "
                f"Subject: {case.subject}"
            ),
            notification_type=NotificationType.assignment,
            entity_type="case",
            entity_id=case.id,
            db=db,
        )

    def notify_deadline_approaching(
        self,
        case: Case,
        days_remaining: int,
        db: Session,
    ) -> None:
        """Notify all current assignees that a deadline is approaching."""
        from app.models.case import CaseAssignment
        assignments = (
            db.query(CaseAssignment)
            .filter(
                CaseAssignment.case_id == case.id,
                CaseAssignment.is_current == True,  # noqa: E712
            )
            .all()
        )
        for assignment in assignments:
            self.create_notification(
                user_id=assignment.assigned_to_id,
                title="Deadline Approaching",
                message=(
                    f"Case {case.case_number} is due in {days_remaining} day(s). "
                    f"Expected disposal: {case.expected_disposal_date}"
                ),
                notification_type=NotificationType.deadline_approaching,
                entity_type="case",
                entity_id=case.id,
                db=db,
            )

    def notify_overdue(self, case: Case, db: Session) -> None:
        """Notify assignees that a case is overdue."""
        from app.models.case import CaseAssignment
        assignments = (
            db.query(CaseAssignment)
            .filter(
                CaseAssignment.case_id == case.id,
                CaseAssignment.is_current == True,  # noqa: E712
            )
            .all()
        )
        for assignment in assignments:
            self.create_notification(
                user_id=assignment.assigned_to_id,
                title="Case Overdue",
                message=(
                    f"Case {case.case_number} is overdue. "
                    f"Expected disposal was {case.expected_disposal_date}."
                ),
                notification_type=NotificationType.overdue,
                entity_type="case",
                entity_id=case.id,
                db=db,
            )

    def notify_overlap_alert(
        self,
        alert: OverlapAlert,
        db: Session,
    ) -> None:
        """Notify bureau officers of both cases involved in an overlap alert."""
        from app.models.user import User, UserRole
        from app.models.case import Case as CaseModel

        case1 = db.query(CaseModel).filter(CaseModel.id == alert.case_id_incoming).first()
        case2 = db.query(CaseModel).filter(CaseModel.id == alert.case_id_existing).first()
        if not case1 or not case2:
            return

        bureau_ids = set()
        if case1.bureau_id:
            bureau_ids.add(case1.bureau_id)
        if case2.bureau_id:
            bureau_ids.add(case2.bureau_id)

        if not bureau_ids:
            return

        officers = (
            db.query(User)
            .filter(
                User.bureau_id.in_(list(bureau_ids)),
                User.is_active == True,  # noqa: E712
            )
            .all()
        )

        for officer in officers:
            self.create_notification(
                user_id=officer.id,
                title="Overlap Alert",
                message=(
                    f"Overlap alert {alert.alert_number} detected between "
                    f"cases {case1.case_number} and {case2.case_number}."
                ),
                notification_type=NotificationType.overlap_alert,
                entity_type="overlap_alert",
                entity_id=alert.id,
                db=db,
            )

    def notify_transfer(
        self,
        case: Case,
        from_bureau: Bureau,
        to_bureau: Bureau,
        db: Session,
    ) -> None:
        """Notify officers in the destination bureau about the transfer."""
        from app.models.user import User
        officers = (
            db.query(User)
            .filter(
                User.bureau_id == to_bureau.id,
                User.is_active == True,  # noqa: E712
            )
            .all()
        )
        for officer in officers:
            self.create_notification(
                user_id=officer.id,
                title="Case Transferred to Your Bureau",
                message=(
                    f"Case {case.case_number} has been transferred from "
                    f"{from_bureau.name} to {to_bureau.name}."
                ),
                notification_type=NotificationType.transfer,
                entity_type="case",
                entity_id=case.id,
                db=db,
            )

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_user_notifications(
        self,
        user_id: uuid.UUID,
        page: int,
        page_size: int,
        db: Session,
    ) -> PaginatedResponse:
        q = (
            db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        total = q.count()
        items = q.offset((page - 1) * page_size).limit(page_size).all()
        return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)

    def mark_read(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
        db: Session,
    ) -> Optional[Notification]:
        notif = (
            db.query(Notification)
            .filter(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
            .first()
        )
        if notif:
            notif.is_read = True
            db.flush()
        return notif

    def mark_all_read(self, user_id: uuid.UUID, db: Session) -> int:
        updated = (
            db.query(Notification)
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .update({"is_read": True})
        )
        db.flush()
        return updated

    def get_unread_count(self, user_id: uuid.UUID, db: Session) -> int:
        return (
            db.query(func.count(Notification.id))
            .filter(
                Notification.user_id == user_id,
                Notification.is_read == False,  # noqa: E712
            )
            .scalar()
            or 0
        )
