"""
Dashboard analytics service.

Provides summary counts, trends, bureau workload, institution tables,
and ageing distribution — all computed live from the database via
SQLAlchemy 2.x query patterns.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import func, case as sa_case, Integer, distinct
from sqlalchemy.orm import Session

from app.models.case import Case, CaseStatus
from app.models.complaint import Complaint, ComplaintStatus
from app.models.bureau import Bureau
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapAlertStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class DashboardSummary:
    total_complaints: int = 0
    total_cases: int = 0
    active_cases: int = 0
    pending_cases: int = 0
    under_process_cases: int = 0
    awaiting_info_cases: int = 0
    transferred_cases: int = 0
    escalated_cases: int = 0
    disposed_cases: int = 0
    closed_cases: int = 0
    overdue_cases: int = 0
    overlap_alerts_pending: int = 0
    overlap_alerts_total: int = 0


@dataclass
class TrendPoint:
    month: str          # "YYYY-MM"
    complaints_received: int = 0
    cases_disposed: int = 0


@dataclass
class WorkloadEntry:
    bureau_id: str
    bureau_name: str
    total_cases: int = 0
    active_cases: int = 0
    assigned_officers: int = 0


@dataclass
class InstitutionTableEntry:
    institution_id: str
    institution_name: str
    permanent_id: Optional[str]
    total_cases: int = 0
    active_cases: int = 0
    disposed_cases: int = 0
    overlap_count: int = 0


@dataclass
class PaginatedResponse:
    items: list
    total: int
    page: int
    page_size: int
    pages: int = field(init=False)

    def __post_init__(self):
        self.pages = (self.total + self.page_size - 1) // self.page_size if self.page_size else 0


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class DashboardService:
    """All dashboard analytics queries live here."""

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(
        self,
        filters: dict,
        user: Any,
        db: Session,
    ) -> DashboardSummary:
        """Return aggregate counts across the whole system (or per bureau)."""
        bureau_filter = filters.get("bureau_id")

        # --- Complaints ---
        cq = db.query(func.count(Complaint.id))
        if bureau_filter:
            cq = cq.filter(Complaint.bureau_id == bureau_filter)
        total_complaints = cq.scalar() or 0

        # --- Cases ---
        def _case_count(*status_filters):
            q = db.query(func.count(Case.id))
            if bureau_filter:
                q = q.filter(Case.bureau_id == bureau_filter)
            if status_filters:
                q = q.filter(Case.status.in_(status_filters))
            return q.scalar() or 0

        total_cases = _case_count()
        pending_cases = _case_count(CaseStatus.pending_assignment)
        under_process_cases = _case_count(CaseStatus.under_process)
        awaiting_info_cases = _case_count(CaseStatus.awaiting_information)
        transferred_cases = _case_count(CaseStatus.transferred)
        escalated_cases = _case_count(CaseStatus.escalated)
        disposed_cases = _case_count(CaseStatus.disposed)
        closed_cases = _case_count(CaseStatus.closed)

        active_cases = (
            pending_cases
            + under_process_cases
            + awaiting_info_cases
            + transferred_cases
            + escalated_cases
            + _case_count(CaseStatus.received)
        )

        # Overdue: has expected_disposal_date in the past and is not closed/disposed
        today = date.today()
        oq = db.query(func.count(Case.id)).filter(
            Case.expected_disposal_date < today,
            Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
        )
        if bureau_filter:
            oq = oq.filter(Case.bureau_id == bureau_filter)
        overdue_cases = oq.scalar() or 0

        # --- Overlap alerts ---
        overlap_alerts_pending = (
            db.query(func.count(OverlapAlert.id))
            .filter(OverlapAlert.status == OverlapAlertStatus.pending_review)
            .scalar()
            or 0
        )
        overlap_alerts_total = db.query(func.count(OverlapAlert.id)).scalar() or 0

        return DashboardSummary(
            total_complaints=total_complaints,
            total_cases=total_cases,
            active_cases=active_cases,
            pending_cases=pending_cases,
            under_process_cases=under_process_cases,
            awaiting_info_cases=awaiting_info_cases,
            transferred_cases=transferred_cases,
            escalated_cases=escalated_cases,
            disposed_cases=disposed_cases,
            closed_cases=closed_cases,
            overdue_cases=overdue_cases,
            overlap_alerts_pending=overlap_alerts_pending,
            overlap_alerts_total=overlap_alerts_total,
        )

    # ------------------------------------------------------------------
    # Monthly trends
    # ------------------------------------------------------------------

    def get_monthly_trends(
        self,
        filters: dict,
        db: Session,
    ) -> list[TrendPoint]:
        """Complaints received and cases disposed per month for last 12 months."""
        today = date.today()
        twelve_months_ago = today.replace(day=1) - timedelta(days=365)

        # Complaints received by month
        from sqlalchemy import extract, cast
        complaint_rows = (
            db.query(
                func.strftime("%Y-%m", Complaint.created_at).label("month"),
                func.count(Complaint.id).label("cnt"),
            )
            .filter(Complaint.created_at >= twelve_months_ago)
            .group_by("month")
            .all()
        )
        complaint_map = {r.month: r.cnt for r in complaint_rows}

        # Cases disposed by month (disposal_date)
        disposed_rows = (
            db.query(
                func.strftime("%Y-%m", Case.disposal_date).label("month"),
                func.count(Case.id).label("cnt"),
            )
            .filter(
                Case.disposal_date.isnot(None),
                Case.disposal_date >= twelve_months_ago,
            )
            .group_by("month")
            .all()
        )
        disposed_map = {r.month: r.cnt for r in disposed_rows}

        # Build 12-month series
        points: list[TrendPoint] = []
        cursor = twelve_months_ago
        while cursor <= today:
            key = cursor.strftime("%Y-%m")
            points.append(
                TrendPoint(
                    month=key,
                    complaints_received=complaint_map.get(key, 0),
                    cases_disposed=disposed_map.get(key, 0),
                )
            )
            # Advance one month
            if cursor.month == 12:
                cursor = cursor.replace(year=cursor.year + 1, month=1)
            else:
                cursor = cursor.replace(month=cursor.month + 1)

        return points

    # ------------------------------------------------------------------
    # Bureau workload
    # ------------------------------------------------------------------

    def get_bureau_workload(
        self,
        filters: dict,
        db: Session,
    ) -> list[WorkloadEntry]:
        from app.models.case import CaseAssignment

        _active = [
            CaseStatus.received,
            CaseStatus.pending_assignment,
            CaseStatus.under_process,
            CaseStatus.awaiting_information,
            CaseStatus.transferred,
            CaseStatus.escalated,
        ]

        bureaus: list[Bureau] = db.query(Bureau).filter(Bureau.is_active == True).all()  # noqa: E712

        result: list[WorkloadEntry] = []
        for bureau in bureaus:
            total = (
                db.query(func.count(Case.id))
                .filter(Case.bureau_id == bureau.id)
                .scalar()
                or 0
            )
            active = (
                db.query(func.count(Case.id))
                .filter(Case.bureau_id == bureau.id, Case.status.in_(_active))
                .scalar()
                or 0
            )
            # Count distinct active assignees
            assigned = (
                db.query(func.count(distinct(CaseAssignment.assigned_to_id)))
                .join(Case, CaseAssignment.case_id == Case.id)
                .filter(
                    Case.bureau_id == bureau.id,
                    CaseAssignment.is_current == True,  # noqa: E712
                )
                .scalar()
                or 0
            )
            result.append(
                WorkloadEntry(
                    bureau_id=str(bureau.id),
                    bureau_name=bureau.name,
                    total_cases=total,
                    active_cases=active,
                    assigned_officers=assigned,
                )
            )

        return result

    # ------------------------------------------------------------------
    # Institution table
    # ------------------------------------------------------------------

    def get_institution_table(
        self,
        filters: dict,
        pagination: dict,
        db: Session,
    ) -> PaginatedResponse:
        page = pagination.get("page", 1)
        page_size = pagination.get("page_size", 20)

        institutions = (
            db.query(Institution)
            .filter(Institution.is_active == True)  # noqa: E712
            .order_by(Institution.name)
            .all()
        )

        entries: list[InstitutionTableEntry] = []
        for inst in institutions:
            total_c = (
                db.query(func.count(Case.id))
                .filter(Case.institution_id == inst.id)
                .scalar()
                or 0
            )
            active_c = (
                db.query(func.count(Case.id))
                .filter(
                    Case.institution_id == inst.id,
                    Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
                )
                .scalar()
                or 0
            )
            disposed_c = (
                db.query(func.count(Case.id))
                .filter(
                    Case.institution_id == inst.id,
                    Case.status.in_([CaseStatus.disposed, CaseStatus.closed]),
                )
                .scalar()
                or 0
            )
            overlaps = (
                db.query(func.count(OverlapAlert.id))
                .filter(OverlapAlert.institution_id == inst.id)
                .scalar()
                or 0
            )
            entries.append(
                InstitutionTableEntry(
                    institution_id=str(inst.id),
                    institution_name=inst.name,
                    permanent_id=inst.permanent_id,
                    total_cases=total_c,
                    active_cases=active_c,
                    disposed_cases=disposed_c,
                    overlap_count=overlaps,
                )
            )

        total = len(entries)
        start = (page - 1) * page_size
        end = start + page_size
        return PaginatedResponse(
            items=entries[start:end],
            total=total,
            page=page,
            page_size=page_size,
        )

    # ------------------------------------------------------------------
    # Ageing distribution
    # ------------------------------------------------------------------

    def get_ageing_distribution(
        self,
        filters: dict,
        db: Session,
    ) -> dict:
        """Bucket active cases by their age in days."""
        from app.models.case import CaseStatus as CS

        _active = [
            CS.received,
            CS.pending_assignment,
            CS.under_process,
            CS.awaiting_information,
            CS.transferred,
            CS.escalated,
        ]

        cases: list[Case] = (
            db.query(Case)
            .filter(Case.status.in_(_active))
            .all()
        )

        buckets = {
            "0_7": 0,
            "8_30": 0,
            "31_60": 0,
            "61_90": 0,
            "91_plus": 0,
        }

        today = date.today()
        for c in cases:
            age = (today - c.created_at.date()).days
            if age <= 7:
                buckets["0_7"] += 1
            elif age <= 30:
                buckets["8_30"] += 1
            elif age <= 60:
                buckets["31_60"] += 1
            elif age <= 90:
                buckets["61_90"] += 1
            else:
                buckets["91_plus"] += 1

        return buckets
