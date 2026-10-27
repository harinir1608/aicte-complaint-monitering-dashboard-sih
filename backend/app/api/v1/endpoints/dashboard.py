from __future__ import annotations

import math
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus
from app.models.complaint import Complaint
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapAlertStatus
from app.models.conflict import ConflictAlert, ConflictStatus as ConflictStatusEnum
from app.models.user import User
from app.schemas.dashboard import (
    AgeingBucket,
    DashboardSummary,
    InstitutionTableEntry,
    OverlapSummary,
    PaginatedInstitutionTable,
    TrendPoint,
    WorkloadEntry,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = datetime.now(timezone.utc).date()

    def count_cases(status_val=None):
        stmt = select(func.count(Case.id))
        if status_val:
            stmt = stmt.where(Case.status == status_val)
        return db.execute(stmt).scalar_one()

    total_complaints = db.execute(select(func.count(Complaint.id))).scalar_one()
    total_cases = count_cases()

    active_statuses = [
        CaseStatus.received,
        CaseStatus.pending_assignment,
        CaseStatus.under_process,
        CaseStatus.awaiting_information,
        CaseStatus.transferred,
        CaseStatus.escalated,
    ]
    active_cases = db.execute(
        select(func.count(Case.id)).where(Case.status.in_(active_statuses))
    ).scalar_one()

    overdue_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.expected_disposal_date < today,
            Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
        )
    ).scalar_one()

    def count_overlap(status_val):
        return db.execute(
            select(func.count(OverlapAlert.id)).where(OverlapAlert.status == status_val)
        ).scalar_one()

    approaching_deadline = db.execute(
        select(func.count(Case.id)).where(
            Case.expected_disposal_date >= today,
            Case.expected_disposal_date <= today + timedelta(days=7),
            Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
        )
    ).scalar_one()

    conflict_warnings_unresolved = db.execute(
        select(func.count(ConflictAlert.id)).where(
            ConflictAlert.status.in_([ConflictStatusEnum.open, ConflictStatusEnum.acknowledged])
        )
    ).scalar_one()

    return DashboardSummary(
        total_complaints=total_complaints,
        total_cases=total_cases,
        active_cases=active_cases,
        pending_assignment=count_cases(CaseStatus.pending_assignment),
        under_process=count_cases(CaseStatus.under_process),
        awaiting_information=count_cases(CaseStatus.awaiting_information),
        transferred=count_cases(CaseStatus.transferred),
        escalated=count_cases(CaseStatus.escalated),
        disposed=count_cases(CaseStatus.disposed),
        closed=count_cases(CaseStatus.closed),
        overdue_cases=overdue_cases,
        cases_approaching_deadline=approaching_deadline,
        overlaps_pending_review=count_overlap(OverlapAlertStatus.pending_review),
        overlaps_confirmed=count_overlap(OverlapAlertStatus.confirmed_related),
        overlaps_false_positive=count_overlap(OverlapAlertStatus.false_positive),
        conflict_warnings_unresolved=conflict_warnings_unresolved,
    )


@router.get("/trends", response_model=List[TrendPoint])
def get_trends(
    months: int = Query(12, ge=1, le=36),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return monthly intake and disposal counts for the last N months."""
    # Complaints intake per month
    intake_rows = db.execute(
        select(
            extract("year", Complaint.created_at).label("yr"),
            extract("month", Complaint.created_at).label("mo"),
            func.count(Complaint.id).label("cnt"),
        ).group_by("yr", "mo").order_by("yr", "mo")
    ).fetchall()

    # Cases disposed per month
    disposed_rows = db.execute(
        select(
            extract("year", Case.disposal_date).label("yr"),
            extract("month", Case.disposal_date).label("mo"),
            func.count(Case.id).label("cnt"),
        )
        .where(Case.disposal_date != None)
        .group_by("yr", "mo")
        .order_by("yr", "mo")
    ).fetchall()

    # Active cases at end of each month is complex; omit for now, set to 0
    intake_map = {f"{int(r.yr):04d}-{int(r.mo):02d}": int(r.cnt) for r in intake_rows}
    disposed_map = {f"{int(r.yr):04d}-{int(r.mo):02d}": int(r.cnt) for r in disposed_rows}

    all_periods = sorted(set(intake_map) | set(disposed_map))[-months:]

    return [
        TrendPoint(
            period=p,
            intake=intake_map.get(p, 0),
            disposed=disposed_map.get(p, 0),
            active=0,
        )
        for p in all_periods
    ]


@router.get("/workload", response_model=List[WorkloadEntry])
def get_workload(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = datetime.now(timezone.utc).date()

    # Bureau workload
    bureaus = db.execute(select(Bureau).where(Bureau.is_active == True)).scalars().all()
    result = []

    for bureau in bureaus:
        total = db.execute(
            select(func.count(Case.id)).where(Case.bureau_id == bureau.id)
        ).scalar_one()
        active_statuses = [
            CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
            CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
        ]
        active = db.execute(
            select(func.count(Case.id)).where(
                Case.bureau_id == bureau.id, Case.status.in_(active_statuses)
            )
        ).scalar_one()
        overdue = db.execute(
            select(func.count(Case.id)).where(
                Case.bureau_id == bureau.id,
                Case.expected_disposal_date < today,
                Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
            )
        ).scalar_one()
        result.append(WorkloadEntry(
            entity_id=bureau.id,
            entity_name=bureau.name,
            entity_type="bureau",
            total_cases=total,
            active_cases=active,
            overdue_cases=overdue,
        ))

    return result


@router.get("/institution-table", response_model=PaginatedInstitutionTable)
def get_institution_table(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = datetime.now(timezone.utc).date()
    stmt = select(Institution).where(Institution.is_active == True)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size
    institutions = db.execute(stmt.order_by(Institution.name).offset(offset).limit(page_size)).scalars().all()

    items = []
    active_statuses = [
        CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
        CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
    ]
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
        overdue_cases = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == inst.id,
                Case.expected_disposal_date < today,
                Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
            )
        ).scalar_one()
        overlap_count = db.execute(
            select(func.count(OverlapAlert.id)).where(
                OverlapAlert.institution_id == inst.id
            )
        ).scalar_one()

        # Latest activity: most recent case updated_at
        latest_row = db.execute(
            select(func.max(Case.updated_at)).where(Case.institution_id == inst.id)
        ).scalar_one()

        items.append(InstitutionTableEntry(
            institution_id=inst.id,
            institution_name=inst.name,
            permanent_id=inst.permanent_id,
            total_complaints=total_complaints,
            total_cases=total_cases,
            active_cases=active_cases,
            overdue_cases=overdue_cases,
            overlap_count=overlap_count,
            latest_activity=latest_row,
        ))

    return PaginatedInstitutionTable(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/ageing", response_model=List[AgeingBucket])
def get_ageing(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    today = datetime.now(timezone.utc).date()

    active_statuses = [
        CaseStatus.received, CaseStatus.pending_assignment, CaseStatus.under_process,
        CaseStatus.awaiting_information, CaseStatus.transferred, CaseStatus.escalated,
    ]
    cases = db.execute(
        select(Case.created_at).where(Case.status.in_(active_statuses))
    ).fetchall()

    buckets = {"0-30 days": 0, "31-60 days": 0, "61-90 days": 0, "91-180 days": 0, "180+ days": 0}
    for row in cases:
        age = (today - row[0].date()).days
        if age <= 30:
            buckets["0-30 days"] += 1
        elif age <= 60:
            buckets["31-60 days"] += 1
        elif age <= 90:
            buckets["61-90 days"] += 1
        elif age <= 180:
            buckets["91-180 days"] += 1
        else:
            buckets["180+ days"] += 1

    total_count = len(cases)
    return [
        AgeingBucket(
            bucket=k,
            count=v,
            percentage=round((v / total_count * 100) if total_count > 0 else 0, 1),
        )
        for k, v in buckets.items()
    ]
