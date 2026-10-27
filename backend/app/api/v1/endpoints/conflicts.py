from __future__ import annotations

import math
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, require_admin
from app.models.conflict import ConflictAlert, ConflictStatus
from app.models.institution import Institution
from app.models.user import User
from app.schemas.conflict import (
    ConflictAlertDetail,
    ConflictAlertListItem,
    ConflictReviewRequest,
    PaginatedConflictAlerts,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/conflicts", tags=["Conflicts"])


def _enrich_item(alert: ConflictAlert, db: Session) -> dict:
    institution_name = None
    if alert.institution_id:
        inst = db.get(Institution, alert.institution_id)
        institution_name = inst.name if inst else None
    return {
        **{c.key: getattr(alert, c.key) for c in alert.__table__.columns},
        "institution_name": institution_name,
    }


@router.get("", response_model=PaginatedConflictAlerts)
def list_conflicts(
    institution_id: Optional[uuid.UUID] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    bureau_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    stmt = select(ConflictAlert)
    if institution_id:
        stmt = stmt.where(ConflictAlert.institution_id == institution_id)
    if severity:
        stmt = stmt.where(ConflictAlert.severity == severity)
    if status:
        stmt = stmt.where(ConflictAlert.status == status)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    alerts = db.execute(
        stmt.order_by(ConflictAlert.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    items = []
    for alert in alerts:
        institution_name = None
        if alert.institution_id:
            inst = db.get(Institution, alert.institution_id)
            institution_name = inst.name if inst else None
        item = ConflictAlertListItem.model_validate(alert)
        item.institution_name = institution_name  # type: ignore[assignment]
        # Filter by bureau_id if provided (JSON field check)
        if bureau_id and (not alert.bureau_ids or bureau_id not in alert.bureau_ids):
            continue
        items.append(item)

    return PaginatedConflictAlerts(
        items=items,
        total=len(items),
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{conflict_id}", response_model=ConflictAlertDetail)
def get_conflict(
    conflict_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.get(ConflictAlert, conflict_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Conflict alert not found")

    institution_name = None
    if alert.institution_id:
        inst = db.get(Institution, alert.institution_id)
        institution_name = inst.name if inst else None

    coordination_owner_name = None
    if alert.coordination_owner:
        coordination_owner_name = alert.coordination_owner.full_name

    detail = ConflictAlertDetail.model_validate(alert)
    detail.institution_name = institution_name  # type: ignore[assignment]
    detail.coordination_owner_name = coordination_owner_name  # type: ignore[assignment]
    return detail


@router.post("/{conflict_id}/review", response_model=ConflictAlertDetail)
def review_conflict(
    conflict_id: uuid.UUID,
    data: ConflictReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alert = db.get(ConflictAlert, conflict_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Conflict alert not found")

    action_map = {
        "acknowledge": ConflictStatus.acknowledged,
        "resolve": ConflictStatus.resolved,
        "dismiss": ConflictStatus.dismissed,
        "assign": None,  # status stays as-is, just update owner
    }

    if data.action not in action_map:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid action '{data.action}'. Must be one of: acknowledge, assign, resolve, dismiss.",
        )

    new_status = action_map[data.action]
    if new_status is not None:
        alert.status = new_status

    if data.resolution_note:
        alert.resolution_note = data.resolution_note

    if data.coordination_owner_id:
        alert.coordination_owner_id = data.coordination_owner_id

    if data.action in ("resolve", "dismiss"):
        alert.resolved_by_id = current_user.id
        alert.resolved_at = datetime.now(timezone.utc)

    log_action(
        entity_type="conflict_alert",
        entity_id=conflict_id,
        action=f"conflict_{data.action}d",
        actor=current_user,
        new_val={
            "action": data.action,
            "resolution_note": data.resolution_note,
            "coordination_owner_id": str(data.coordination_owner_id) if data.coordination_owner_id else None,
        },
        db=db,
    )
    db.commit()
    db.refresh(alert)

    institution_name = None
    if alert.institution_id:
        inst = db.get(Institution, alert.institution_id)
        institution_name = inst.name if inst else None

    detail = ConflictAlertDetail.model_validate(alert)
    detail.institution_name = institution_name  # type: ignore[assignment]
    return detail


@router.post("/scan", status_code=202)
def trigger_conflict_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Manually trigger a global conflict scan (admin only)."""
    from app.services.conflict_service import run_global_conflict_scan
    count = run_global_conflict_scan(db)
    return {"message": f"Conflict scan complete. {count} new alert(s) created.", "alerts_created": count}
