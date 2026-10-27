from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.case import CaseStatus, CasePriority, CaseActionType, RelationshipType


# ── Assignment schemas ─────────────────────────────────────────────────────────

class CaseAssignmentCreate(BaseModel):
    officer_id: uuid.UUID
    notes: Optional[str] = None


class CaseAssignmentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    assigned_to_id: uuid.UUID
    assigned_by_id: Optional[uuid.UUID]
    assigned_at: datetime
    notes: Optional[str]
    is_current: bool

    model_config = {"from_attributes": True}


# ── Action schemas ─────────────────────────────────────────────────────────────

class CaseActionCreate(BaseModel):
    action_type: CaseActionType = CaseActionType.note
    description: Optional[str] = None


class CaseActionResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    action_type: CaseActionType
    description: Optional[str]
    performed_by_id: Optional[uuid.UUID]
    performed_at: datetime
    old_status: Optional[str]
    new_status: Optional[str]

    model_config = {"from_attributes": True}


# ── Related case schemas ───────────────────────────────────────────────────────

class RelatedCaseCreate(BaseModel):
    related_case_id: uuid.UUID
    relationship_type: RelationshipType = RelationshipType.other
    rationale: Optional[str] = None
    coordination_notes: Optional[str] = None


class RelatedCaseResponse(BaseModel):
    id: uuid.UUID
    case_id_1: uuid.UUID
    case_id_2: uuid.UUID
    relationship_type: RelationshipType
    rationale: Optional[str]
    linked_by_id: Optional[uuid.UUID]
    linked_at: datetime
    coordination_notes: Optional[str]

    model_config = {"from_attributes": True}


# ── Transfer and escalate ─────────────────────────────────────────────────────

class CaseTransferRequest(BaseModel):
    target_bureau_id: uuid.UUID
    reason: str = Field(..., min_length=1)


class CaseEscalateRequest(BaseModel):
    reason: str = Field(..., min_length=1)
    escalate_to_id: Optional[uuid.UUID] = None


# ── Status update ──────────────────────────────────────────────────────────────

class CaseStatusUpdate(BaseModel):
    new_status: CaseStatus
    remarks: Optional[str] = None


# ── Document schemas ──────────────────────────────────────────────────────────

class CaseDocumentResponse(BaseModel):
    id: uuid.UUID
    case_id: uuid.UUID
    filename: str
    storage_key: str
    file_size: Optional[int]
    content_type: Optional[str]
    uploaded_by_id: Optional[uuid.UUID]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── Case CRUD schemas ──────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    complaint_id: Optional[uuid.UUID] = None
    institution_id: Optional[uuid.UUID] = None
    bureau_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    priority: CasePriority = CasePriority.normal
    sla_days: Optional[int] = Field(None, ge=1)
    expected_disposal_date: Optional[date] = None


class CaseUpdate(BaseModel):
    institution_id: Optional[uuid.UUID] = None
    bureau_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    priority: Optional[CasePriority] = None
    sla_days: Optional[int] = Field(None, ge=1)
    expected_disposal_date: Optional[date] = None
    disposal_date: Optional[date] = None
    disposal_remarks: Optional[str] = None


class CaseResponse(BaseModel):
    id: uuid.UUID
    case_number: str
    complaint_id: Optional[uuid.UUID]
    institution_id: Optional[uuid.UUID]
    bureau_id: Optional[uuid.UUID]
    category_id: Optional[uuid.UUID]
    subject: str
    description: Optional[str]
    status: CaseStatus
    priority: CasePriority
    sla_days: Optional[int]
    expected_disposal_date: Optional[date]
    disposal_date: Optional[date]
    disposal_remarks: Optional[str]
    created_by_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    assignments: List[CaseAssignmentResponse] = []
    actions: List[CaseActionResponse] = []
    documents: List[CaseDocumentResponse] = []

    model_config = {"from_attributes": True}


class CaseListItem(BaseModel):
    id: uuid.UUID
    case_number: str
    complaint_id: Optional[uuid.UUID]
    institution_id: Optional[uuid.UUID]
    bureau_id: Optional[uuid.UUID]
    subject: str
    status: CaseStatus
    priority: CasePriority
    expected_disposal_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination wrapper ─────────────────────────────────────────────────────────

class PaginatedCases(BaseModel):
    items: List[CaseListItem]
    total: int
    page: int
    page_size: int
    pages: int
