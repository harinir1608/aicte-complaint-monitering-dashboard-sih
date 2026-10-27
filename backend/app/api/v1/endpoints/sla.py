from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, require_admin
from app.models.notification import SLARule
from app.models.user import User
from app.services.audit_service import log_action


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class SLARuleCreate(BaseModel):
    bureau_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    priority: Optional[str] = Field(None, max_length=50)
    sla_days: int = Field(..., ge=1)
    warning_days: int = Field(5, ge=1)
    escalation_days: int = Field(2, ge=1)
    is_active: bool = True


class SLARuleUpdate(BaseModel):
    bureau_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    priority: Optional[str] = Field(None, max_length=50)
    sla_days: Optional[int] = Field(None, ge=1)
    warning_days: Optional[int] = Field(None, ge=1)
    escalation_days: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class SLARuleResponse(BaseModel):
    id: uuid.UUID
    bureau_id: Optional[uuid.UUID]
    category_id: Optional[uuid.UUID]
    priority: Optional[str]
    sla_days: int
    warning_days: int
    escalation_days: int
    is_active: bool

    model_config = {"from_attributes": True}


# ── Router ─────────────────────────────────────────────────────────────────────

router = APIRouter(prefix="/sla-rules", tags=["SLA Rules"])


@router.get("", response_model=List[SLARuleResponse])
def list_sla_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    rules = db.execute(select(SLARule).order_by(SLARule.created_at)).scalars().all()
    return [SLARuleResponse.model_validate(r) for r in rules]


@router.post("", response_model=SLARuleResponse, status_code=201)
def create_sla_rule(
    data: SLARuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rule = SLARule(**data.model_dump())
    db.add(rule)
    db.flush()
    log_action(
        entity_type="sla_rule",
        entity_id=rule.id,
        action="created",
        actor=current_user,
        new_val=data.model_dump(),
        db=db,
    )
    db.commit()
    db.refresh(rule)
    return SLARuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=SLARuleResponse)
def update_sla_rule(
    rule_id: uuid.UUID,
    data: SLARuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    rule = db.get(SLARule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="SLA rule not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    log_action(
        entity_type="sla_rule",
        entity_id=rule.id,
        action="updated",
        actor=current_user,
        new_val=data.model_dump(exclude_unset=True),
        db=db,
    )
    db.commit()
    db.refresh(rule)
    return SLARuleResponse.model_validate(rule)
