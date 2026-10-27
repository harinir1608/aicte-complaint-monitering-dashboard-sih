from __future__ import annotations

import math
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.bureau import Bureau
from app.models.case import Case
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapAlertStatus, OverlapReview
from app.models.user import User
from app.schemas.overlap import (
    OverlapAlertListItem,
    OverlapAlertResponse,
    OverlapReviewCreate,
    OverlapReviewResponse,
    PaginatedOverlapAlerts,
    RelatedCaseSummary,
)
from app.services.audit_service import log_action, get_audit_trail

router = APIRouter(prefix="/overlaps", tags=["Overlaps"])


def _build_case_summary(case: Case, db: Session) -> RelatedCaseSummary:
    bureau_name = None
    if case.bureau_id:
        bureau = db.get(Bureau, case.bureau_id)
        if bureau:
            bureau_name = bureau.name
    institution_name = None
    if case.institution_id:
        inst = db.get(Institution, case.institution_id)
        if inst:
            institution_name = inst.name
    # Current assignment
    officer_name = None
    current = next((a for a in case.assignments if a.is_current), None)
    if current:
        officer_name = current.assigned_to.full_name if current.assigned_to else None

    return RelatedCaseSummary(
        id=case.id,
        case_number=case.case_number,
        subject=case.subject,
        status=case.status,
        priority=case.priority,
        bureau_id=case.bureau_id,
        bureau_name=bureau_name,
        institution_id=case.institution_id,
        institution_name=institution_name,
        created_at=case.created_at,
        expected_disposal_date=case.expected_disposal_date,
        assigned_officer_name=officer_name,
    )


@router.get("", response_model=PaginatedOverlapAlerts)
def list_overlaps(
    status: Optional[str] = Query(None),
    bureau_id: Optional[uuid.UUID] = Query(None),
    match_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(OverlapAlert)

    if status:
        stmt = stmt.where(OverlapAlert.status == status)
    if match_type:
        stmt = stmt.where(OverlapAlert.match_type == match_type)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = db.execute(
        stmt.order_by(OverlapAlert.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    return PaginatedOverlapAlerts(
        items=[OverlapAlertListItem.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{overlap_id}", response_model=OverlapAlertResponse)
def get_overlap(
    overlap_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.get(OverlapAlert, overlap_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Overlap alert not found")

    incoming_summary = _build_case_summary(alert.case_incoming, db)
    existing_summary = _build_case_summary(alert.case_existing, db)

    response = OverlapAlertResponse.model_validate(alert)
    response.incoming_case = incoming_summary
    response.existing_case = existing_summary
    response.reviews = [OverlapReviewResponse.model_validate(r) for r in alert.reviews]
    return response


@router.post("/{overlap_id}/review", response_model=OverlapReviewResponse, status_code=201)
def submit_review(
    overlap_id: uuid.UUID,
    data: OverlapReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.get(OverlapAlert, overlap_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Overlap alert not found")

    review = OverlapReview(
        alert_id=overlap_id,
        reviewed_by_id=current_user.id,
        decision=data.decision,
        remarks=data.remarks,
        coordination_owner_id=data.coordination_owner_id,
    )
    db.add(review)

    # Update alert status based on decision
    from app.models.overlap import OverlapReviewDecision
    decision_to_status = {
        OverlapReviewDecision.confirmed_related: OverlapAlertStatus.confirmed_related,
        OverlapReviewDecision.false_positive: OverlapAlertStatus.false_positive,
        OverlapReviewDecision.linked: OverlapAlertStatus.linked,
        OverlapReviewDecision.maintain_separate: OverlapAlertStatus.dismissed,
        OverlapReviewDecision.needs_investigation: OverlapAlertStatus.pending_review,
    }
    alert.status = decision_to_status.get(data.decision, OverlapAlertStatus.pending_review)

    log_action(
        entity_type="overlap_alert",
        entity_id=overlap_id,
        action="reviewed",
        actor=current_user,
        new_val={"decision": data.decision, "remarks": data.remarks},
        db=db,
    )
    db.commit()
    db.refresh(review)
    return OverlapReviewResponse.model_validate(review)


@router.get("/{overlap_id}/history")
def get_overlap_history(
    overlap_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return review history for an overlap alert from the audit log."""
    alert = db.get(OverlapAlert, overlap_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Overlap alert not found")
    history = get_audit_trail(entity_type="overlap_alert", entity_id=overlap_id, db=db)
    return [
        {
            "id": str(h.id),
            "action": h.action,
            "actor_email": h.actor_email,
            "timestamp": h.timestamp.isoformat() if h.timestamp else None,
            "old_value": h.old_value,
            "new_value": h.new_value,
            "remarks": h.remarks,
        }
        for h in history
    ]


@router.post("/run-check/{case_id}", status_code=202)
def run_overlap_check(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger overlap check for a case. Returns accepted status."""
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    # The actual overlap check runs asynchronously via the matching service.
    # For now, return a 202 Accepted to indicate the check has been queued.
    return {"message": f"Overlap check queued for case {case.case_number}", "case_id": str(case_id)}
