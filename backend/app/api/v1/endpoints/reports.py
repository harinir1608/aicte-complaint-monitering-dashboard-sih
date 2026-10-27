from __future__ import annotations

import csv
import io
import uuid
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.bureau import Bureau, Region
from app.models.case import Case, CaseStatus
from app.models.complaint import Complaint
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapReview
from app.models.user import User
from app.schemas.report import (
    AgeingReport,
    AgeingReportRow,
    InstitutionReport,
    InstitutionReportRow,
    OverlapReport,
    OverlapReportRow,
    ReportFilters,
    WorkloadReport,
    WorkloadReportRow,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


def _apply_report_filters(stmt, filters: ReportFilters, model=Case):
    if filters.date_from:
        stmt = stmt.where(model.created_at >= filters.date_from)
    if filters.date_to:
        stmt = stmt.where(model.created_at <= filters.date_to)
    if filters.bureau_id and hasattr(model, "bureau_id"):
        stmt = stmt.where(model.bureau_id == filters.bureau_id)
    if filters.status and hasattr(model, "status"):
        stmt = stmt.where(model.status == filters.status)
    if filters.priority and hasattr(model, "priority"):
        stmt = stmt.where(model.priority == filters.priority)
    if filters.category_id and hasattr(model, "category_id"):
        stmt = stmt.where(model.category_id == filters.category_id)
    return stmt


@router.get("/institutions")
def institution_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = ReportFilters(
        date_from=date_from, date_to=date_to, bureau_id=bureau_id, region_id=region_id
    )

    stmt = select(Institution)
    if region_id:
        stmt = stmt.where(Institution.region_id == region_id)
    institutions = db.execute(stmt).scalars().all()

    today = datetime.now(timezone.utc).date()
    active_statuses = [
        CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
        CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
    ]
    rows = []
    for inst in institutions:
        total_complaints = db.execute(
            select(func.count(Complaint.id)).where(Complaint.institution_id == inst.id)
        ).scalar_one()
        total_cases = db.execute(
            select(func.count(Case.id)).where(Case.institution_id == inst.id)
        ).scalar_one()
        active_cases = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == inst.id, Case.status.in_(active_statuses)
            )
        ).scalar_one()
        disposed_cases = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == inst.id, Case.status == CaseStatus.disposed
            )
        ).scalar_one()
        overdue_cases = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == inst.id,
                Case.expected_disposal_date < today,
                Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
            )
        ).scalar_one()
        overlap_count = db.execute(
            select(func.count(OverlapAlert.id)).where(OverlapAlert.institution_id == inst.id)
        ).scalar_one()
        latest = db.execute(
            select(func.max(Case.updated_at)).where(Case.institution_id == inst.id)
        ).scalar_one()

        region_name = None
        if inst.region_id:
            r = db.get(Region, inst.region_id)
            if r:
                region_name = r.name

        rows.append(InstitutionReportRow(
            institution_id=inst.id,
            institution_name=inst.name,
            permanent_id=inst.permanent_id,
            state=inst.state,
            region_name=region_name,
            total_complaints=total_complaints,
            total_cases=total_cases,
            active_cases=active_cases,
            disposed_cases=disposed_cases,
            overdue_cases=overdue_cases,
            overlap_count=overlap_count,
            latest_activity=latest,
        ))

    if format == "csv":
        return _csv_response(
            headers=["institution_id", "institution_name", "permanent_id", "state",
                     "region_name", "total_complaints", "total_cases", "active_cases",
                     "disposed_cases", "overdue_cases", "overlap_count", "latest_activity"],
            rows=[[str(r.institution_id), r.institution_name, r.permanent_id or "",
                   r.state or "", r.region_name or "",
                   r.total_complaints, r.total_cases, r.active_cases,
                   r.disposed_cases, r.overdue_cases, r.overlap_count,
                   str(r.latest_activity) if r.latest_activity else ""] for r in rows],
            filename="institution_report.csv",
        )

    return InstitutionReport(
        filters=filters,
        generated_at=datetime.now(timezone.utc),
        rows=rows,
        total_rows=len(rows),
    )


@router.get("/ageing")
def ageing_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = ReportFilters(date_from=date_from, date_to=date_to, bureau_id=bureau_id)
    today = datetime.now(timezone.utc).date()

    active_statuses = [
        CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
        CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
    ]
    stmt = select(Case).where(Case.status.in_(active_statuses))
    if bureau_id:
        stmt = stmt.where(Case.bureau_id == bureau_id)
    if date_from:
        stmt = stmt.where(Case.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Case.created_at <= date_to)

    cases = db.execute(stmt).scalars().all()
    rows = []
    overdue_count = 0
    for case in cases:
        age_days = (today - case.created_at.date()).days
        is_overdue = bool(case.expected_disposal_date and case.expected_disposal_date < today)
        if is_overdue:
            overdue_count += 1

        bureau_name = None
        if case.bureau_id:
            b = db.get(Bureau, case.bureau_id)
            if b:
                bureau_name = b.name

        institution_name = None
        if case.institution_id:
            inst = db.get(Institution, case.institution_id)
            if inst:
                institution_name = inst.name

        rows.append(AgeingReportRow(
            case_id=case.id,
            case_number=case.case_number,
            institution_name=institution_name,
            bureau_name=bureau_name,
            subject=case.subject,
            status=case.status.value,
            priority=case.priority.value,
            created_at=case.created_at,
            expected_disposal_date=case.expected_disposal_date,
            age_days=age_days,
            is_overdue=is_overdue,
        ))

    if format == "csv":
        return _csv_response(
            headers=["case_number", "institution_name", "bureau_name", "subject",
                     "status", "priority", "created_at", "expected_disposal_date",
                     "age_days", "is_overdue"],
            rows=[[r.case_number, r.institution_name or "", r.bureau_name or "",
                   r.subject, r.status, r.priority,
                   str(r.created_at), str(r.expected_disposal_date) if r.expected_disposal_date else "",
                   r.age_days, r.is_overdue] for r in rows],
            filename="ageing_report.csv",
        )

    return AgeingReport(
        filters=filters,
        generated_at=datetime.now(timezone.utc),
        rows=rows,
        total_rows=len(rows),
        overdue_count=overdue_count,
    )


@router.get("/overlaps")
def overlaps_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = ReportFilters(date_from=date_from, date_to=date_to, bureau_id=bureau_id)

    stmt = select(OverlapAlert)
    if date_from:
        stmt = stmt.where(OverlapAlert.created_at >= date_from)
    if date_to:
        stmt = stmt.where(OverlapAlert.created_at <= date_to)

    alerts = db.execute(stmt).scalars().all()
    rows = []
    for alert in alerts:
        # Latest review decision
        latest_review = db.execute(
            select(OverlapReview)
            .where(OverlapReview.alert_id == alert.id)
            .order_by(OverlapReview.reviewed_at.desc())
        ).scalar_one_or_none()

        rows.append(OverlapReportRow(
            alert_id=alert.id,
            alert_number=alert.alert_number,
            incoming_case_number=alert.case_incoming.case_number,
            existing_case_number=alert.case_existing.case_number,
            institution_name=alert.institution.name if alert.institution else None,
            match_type=alert.match_type.value,
            match_score=alert.match_score,
            alert_status=alert.status.value,
            review_decision=latest_review.decision.value if latest_review else None,
            reviewed_at=latest_review.reviewed_at if latest_review else None,
            created_at=alert.created_at,
        ))

    if format == "csv":
        return _csv_response(
            headers=["alert_number", "incoming_case", "existing_case", "institution",
                     "match_type", "match_score", "alert_status", "review_decision",
                     "reviewed_at", "created_at"],
            rows=[[r.alert_number, r.incoming_case_number, r.existing_case_number,
                   r.institution_name or "", r.match_type, r.match_score or "",
                   r.alert_status, r.review_decision or "",
                   str(r.reviewed_at) if r.reviewed_at else "",
                   str(r.created_at)] for r in rows],
            filename="overlaps_report.csv",
        )

    return OverlapReport(
        filters=filters,
        generated_at=datetime.now(timezone.utc),
        rows=rows,
        total_rows=len(rows),
    )


@router.get("/workload")
def workload_report(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    format: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    filters = ReportFilters(date_from=date_from, date_to=date_to, bureau_id=bureau_id)

    bureaus_stmt = select(Bureau).where(Bureau.is_active == True)
    if bureau_id:
        bureaus_stmt = bureaus_stmt.where(Bureau.id == bureau_id)
    bureaus = db.execute(bureaus_stmt).scalars().all()

    today = datetime.now(timezone.utc).date()
    active_statuses = [
        CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
        CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
    ]

    rows = []
    for bureau in bureaus:
        cases_stmt = select(Case).where(Case.bureau_id == bureau.id)
        if date_from:
            cases_stmt = cases_stmt.where(Case.created_at >= date_from)
        if date_to:
            cases_stmt = cases_stmt.where(Case.created_at <= date_to)
        cases = db.execute(cases_stmt).scalars().all()

        total = len(cases)
        active = sum(1 for c in cases if c.status in active_statuses)
        disposed = sum(1 for c in cases if c.status == CaseStatus.disposed)
        overdue = sum(1 for c in cases if c.expected_disposal_date and c.expected_disposal_date < today and c.status not in [CaseStatus.disposed, CaseStatus.closed])
        avg_age = None
        if cases:
            avg_age = sum((today - c.created_at.date()).days for c in cases) / len(cases)

        rows.append(WorkloadReportRow(
            entity_type="bureau",
            entity_name=bureau.name,
            total_cases=total,
            active_cases=active,
            disposed_cases=disposed,
            overdue_cases=overdue,
            average_age_days=round(avg_age, 1) if avg_age is not None else None,
        ))

    if format == "csv":
        return _csv_response(
            headers=["bureau", "total_cases", "active_cases", "disposed_cases",
                     "overdue_cases", "average_age_days"],
            rows=[[r.entity_name, r.total_cases, r.active_cases, r.disposed_cases,
                   r.overdue_cases, r.average_age_days or ""] for r in rows],
            filename="workload_report.csv",
        )

    return WorkloadReport(
        filters=filters,
        generated_at=datetime.now(timezone.utc),
        rows=rows,
        total_rows=len(rows),
    )


# ── CSV helper ─────────────────────────────────────────────────────────────────

def _csv_response(headers, rows, filename: str) -> StreamingResponse:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
