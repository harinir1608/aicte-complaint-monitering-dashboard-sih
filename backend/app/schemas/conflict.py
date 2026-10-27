from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.conflict import ConflictSeverity, ConflictStatus


class ConflictAlertListItem(BaseModel):
    id: uuid.UUID
    institution_id: Optional[uuid.UUID]
    institution_name: Optional[str] = None
    case_ids: Optional[List[str]]
    bureau_ids: Optional[List[str]]
    rule_triggered: str
    rule_description: Optional[str]
    severity: ConflictSeverity
    status: ConflictStatus
    recommended_action: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConflictAlertDetail(BaseModel):
    id: uuid.UUID
    institution_id: Optional[uuid.UUID]
    institution_name: Optional[str] = None
    case_ids: Optional[List[str]]
    bureau_ids: Optional[List[str]]
    rule_triggered: str
    rule_description: Optional[str]
    evidence: Optional[Dict[str, Any]]
    severity: ConflictSeverity
    recommended_action: Optional[str]
    coordination_owner_id: Optional[uuid.UUID]
    coordination_owner_name: Optional[str] = None
    status: ConflictStatus
    resolution_note: Optional[str]
    resolved_by_id: Optional[uuid.UUID]
    resolved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConflictReviewRequest(BaseModel):
    action: str  # "acknowledge" | "assign" | "resolve" | "dismiss"
    resolution_note: Optional[str] = None
    coordination_owner_id: Optional[uuid.UUID] = None


class PaginatedConflictAlerts(BaseModel):
    items: List[ConflictAlertListItem]
    total: int
    page: int
    page_size: int
    pages: int
