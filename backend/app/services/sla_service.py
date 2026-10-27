"""
SLA (Service Level Agreement) monitoring service.

Determines the applicable SLA rule for a case, calculates expected disposal
dates, and scans for approaching / overdue deadlines.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus
from app.models.notification import SLARule, Notification, NotificationType

logger = logging.getLogger(__name__)

# Statuses where SLA monitoring is relevant
_ACTIVE_STATUSES = [
    CaseStatus.received,
    CaseStatus.pending_assignment,
    CaseStatus.under_process,
    CaseStatus.awaiting_information,
    CaseStatus.transferred,
    CaseStatus.escalated,
]


class SLAService:
    """Encapsulates all SLA-related logic."""

    # ------------------------------------------------------------------
    # Rule resolution
    # ------------------------------------------------------------------

    def get_applicable_sla(
        self,
        case: Case,
        db: Session,
    ) -> Optional[SLARule]:
        """Return the most specific SLA rule for *case*.

        Specificity order (most specific first):
          1. bureau + category + priority
          2. bureau + category
          3. bureau + priority
          4. bureau (any category / priority)
          5. category + priority
          6. category
          7. global (no bureau, no category)
        """
        all_rules: list[SLARule] = (
            db.query(SLARule).filter(SLARule.is_active == True).all()  # noqa: E712
        )
        if not all_rules:
            return None

        bureau_id = case.bureau_id
        category_id = case.category_id
        priority = case.priority.value if case.priority else None

        candidates: list[tuple[int, SLARule]] = []

        for rule in all_rules:
            score = self._specificity_score(
                rule, bureau_id, category_id, priority
            )
            if score >= 0:
                candidates.append((score, rule))

        if not candidates:
            return None

        # Higher score = more specific
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    @staticmethod
    def _specificity_score(
        rule: SLARule,
        bureau_id,
        category_id,
        priority: Optional[str],
    ) -> int:
        """
        Return a specificity score for *rule* relative to the case attributes.
        Returns -1 if the rule definitely doesn't apply.
        """
        score = 0

        # Bureau match
        if rule.bureau_id is not None:
            if rule.bureau_id != bureau_id:
                return -1
            score += 4
        elif bureau_id is not None:
            pass  # global bureau rule can still apply, no extra points

        # Category match
        if rule.category_id is not None:
            if rule.category_id != category_id:
                return -1
            score += 2
        elif category_id is not None:
            pass

        # Priority match
        if rule.priority is not None:
            if rule.priority != priority:
                return -1
            score += 1

        return score

    # ------------------------------------------------------------------
    # Deadline calculation
    # ------------------------------------------------------------------

    def calculate_expected_disposal(self, case: Case, sla_days: int) -> date:
        """Return the expected disposal date = created_at + sla_days."""
        base = (
            case.created_at.date()
            if hasattr(case.created_at, "date")
            else case.created_at
        )
        return base + timedelta(days=sla_days)

    def is_case_overdue(self, case: Case) -> bool:
        """True if the case has an expected_disposal_date in the past."""
        if not case.expected_disposal_date:
            return False
        if case.status in (CaseStatus.disposed, CaseStatus.closed):
            return False
        return case.expected_disposal_date < date.today()

    # ------------------------------------------------------------------
    # Batch deadline check
    # ------------------------------------------------------------------

    def check_deadlines_and_notify(self, db: Session) -> int:
        """Scan active cases with expected_disposal_date and notify as needed.

        Returns the number of notifications created.
        """
        from app.services.notification_service import NotificationService
        notif_svc = NotificationService()
        count = 0
        today = date.today()

        active_cases: list[Case] = (
            db.query(Case)
            .filter(
                Case.status.in_(_ACTIVE_STATUSES),
                Case.expected_disposal_date.isnot(None),
            )
            .all()
        )

        for case in active_cases:
            days_remaining = (case.expected_disposal_date - today).days
            rule = self.get_applicable_sla(case, db)
            warning_days = rule.warning_days if rule else 5

            if days_remaining < 0:
                # Overdue — check idempotency (one notification per day)
                already_sent = self._already_notified_today(
                    case, NotificationType.overdue, db
                )
                if not already_sent:
                    notif_svc.notify_overdue(case, db)
                    count += 1
            elif days_remaining <= warning_days:
                already_sent = self._already_notified_today(
                    case, NotificationType.deadline_approaching, db
                )
                if not already_sent:
                    notif_svc.notify_deadline_approaching(case, days_remaining, db)
                    count += 1

        if count:
            db.commit()

        return count

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _already_notified_today(
        case: Case,
        notif_type: NotificationType,
        db: Session,
    ) -> bool:
        """True if a notification of *notif_type* for *case* was created today."""
        today_start = datetime.combine(date.today(), datetime.min.time()).replace(
            tzinfo=timezone.utc
        )
        count = (
            db.query(Notification)
            .filter(
                Notification.related_entity_type == "case",
                Notification.related_entity_id == case.id,
                Notification.notification_type == notif_type,
                Notification.created_at >= today_start,
            )
            .count()
        )
        return count > 0
