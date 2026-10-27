from __future__ import annotations

import uuid
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def log_action(
    *,
    entity_type: str,
    entity_id: Optional[uuid.UUID],
    action: str,
    actor: Optional[User],
    old_val: Optional[Any] = None,
    new_val: Optional[Any] = None,
    remarks: Optional[str] = None,
    db: Session,
    request_id: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Create and persist an AuditLog entry.

    The caller is responsible for committing the transaction.
    """
    entry = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor_id=actor.id if actor else None,
        actor_email=actor.email if actor else None,
        old_value=old_val,
        new_value=new_val,
        remarks=remarks,
        request_id=request_id,
        ip_address=ip_address,
    )
    db.add(entry)
    return entry


def get_audit_trail(
    *,
    entity_type: str,
    entity_id: uuid.UUID,
    db: Session,
) -> List[AuditLog]:
    """Return all audit log entries for a specific entity, ordered by timestamp."""
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.entity_type == entity_type,
            AuditLog.entity_id == entity_id,
        )
        .order_by(AuditLog.timestamp.asc())
    )
    return list(db.execute(stmt).scalars().all())
