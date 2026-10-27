from __future__ import annotations

import math
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.models.audit import AuditLog
from app.models.user import User
from app.services.audit_service import get_audit_trail


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: Optional[uuid.UUID]
    action: str
    actor_id: Optional[uuid.UUID]
    actor_email: Optional[str]
    timestamp: datetime
    old_value: Optional[dict]
    new_value: Optional[dict]
    remarks: Optional[str]
    request_id: Optional[str]
    ip_address: Optional[str]

    model_config = {"from_attributes": True}


class PaginatedAuditLogs(BaseModel):
    items: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    pages: int


router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=PaginatedAuditLogs)
def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[uuid.UUID] = Query(None),
    actor_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    stmt = select(AuditLog)
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditLog.entity_id == entity_id)
    if actor_id:
        stmt = stmt.where(AuditLog.actor_id == actor_id)
    if date_from:
        stmt = stmt.where(AuditLog.timestamp >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.timestamp <= date_to)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = db.execute(
        stmt.order_by(AuditLog.timestamp.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    return PaginatedAuditLogs(
        items=[AuditLogResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{entity_type}/{entity_id}", response_model=List[AuditLogResponse])
def get_entity_audit_trail(
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    logs = get_audit_trail(entity_type=entity_type, entity_id=entity_id, db=db)
    return [AuditLogResponse.model_validate(l) for l in logs]
