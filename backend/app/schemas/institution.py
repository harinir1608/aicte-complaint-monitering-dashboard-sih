from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.institution import InstitutionType, AliasType


# ── Alias schemas ─────────────────────────────────────────────────────────────

class InstitutionAliasCreate(BaseModel):
    alias: str = Field(..., min_length=1, max_length=500)
    alias_type: AliasType = AliasType.other
    is_primary: bool = False


class InstitutionAliasResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    alias: str
    alias_type: AliasType
    is_primary: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Institution CRUD schemas ───────────────────────────────────────────────────

class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=500)
    permanent_id: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    region_id: Optional[uuid.UUID] = None
    institution_type: Optional[InstitutionType] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    pin_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    is_active: bool = True


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=500)
    permanent_id: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    district: Optional[str] = Field(None, max_length=100)
    region_id: Optional[uuid.UUID] = None
    institution_type: Optional[InstitutionType] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    pin_code: Optional[str] = Field(None, max_length=20)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class InstitutionResponse(BaseModel):
    id: uuid.UUID
    permanent_id: Optional[str]
    name: str
    state: Optional[str]
    district: Optional[str]
    region_id: Optional[uuid.UUID]
    institution_type: Optional[InstitutionType]
    address: Optional[str]
    city: Optional[str]
    pin_code: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    aliases: List[InstitutionAliasResponse] = []

    model_config = {"from_attributes": True}


class InstitutionListResponse(BaseModel):
    id: uuid.UUID
    permanent_id: Optional[str]
    name: str
    state: Optional[str]
    district: Optional[str]
    institution_type: Optional[InstitutionType]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Institution profile (with case statistics) ────────────────────────────────

class BureauCaseSummary(BaseModel):
    bureau_id: uuid.UUID
    bureau_name: str
    bureau_code: str
    total_cases: int
    active_cases: int
    disposed_cases: int


class CaseHistoryEntry(BaseModel):
    id: uuid.UUID
    case_number: str
    subject: str
    status: str
    priority: str
    bureau_name: Optional[str]
    expected_disposal_date: Optional[str]
    created_at: datetime
    updated_at: datetime


class AssignedOfficerEntry(BaseModel):
    officer_id: uuid.UUID
    officer_name: str
    officer_email: str
    bureau_name: Optional[str]
    case_ids: List[uuid.UUID]


class InstitutionProfile(BaseModel):
    institution: InstitutionResponse
    total_complaints: int
    total_cases: int
    active_cases: int
    pending_cases: int
    under_process_cases: int
    disposed_cases: int
    transferred_cases: int
    escalated_cases: int
    overdue_cases: int
    unresolved_overlap_alerts: int
    bureau_breakdown: List[BureauCaseSummary] = []
    assigned_officers: List[AssignedOfficerEntry] = []
    case_history: List[CaseHistoryEntry] = []
    latest_activity: Optional[datetime] = None


# ── Relationship graph ─────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    node_type: str   # "institution" | "case" | "complaint" | "bureau"
    label: str
    status: Optional[str] = None
    url: Optional[str] = None
    data: Optional[dict] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class InstitutionGraph(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# ── Pagination wrapper ─────────────────────────────────────────────────────────

class PaginatedInstitutions(BaseModel):
    items: List[InstitutionListResponse]
    total: int
    page: int
    page_size: int
    pages: int
