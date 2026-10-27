from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict

from pydantic import BaseModel, Field

from app.models.overlap import MatchType, OverlapAlertStatus, OverlapReviewDecision
from app.models.case import CaseStatus, CasePriority


# ── Related case summary (for side-by-side comparison) ───────────────────────

class RelatedCaseSummary(BaseModel):
    id: uuid.UUID
    case_number: str
    subject: str
    status: CaseStatus
    priority: CasePriority
    bureau_id: Optional[uuid.UUID]
    bureau_name: Optional[str]
    institution_id: Optional[uuid.UUID]
    institution_name: Optional[str]
    created_at: datetime
    expected_disposal_date: Optional[Any] = None
    assigned_officer_name: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Overlap alert schemas ──────────────────────────────────────────────────────

class OverlapAlertListItem(BaseModel):
    id: uuid.UUID
    alert_number: str
    case_id_incoming: uuid.UUID
    case_id_existing: uuid.UUID
    institution_id: Optional[uuid.UUID]
    match_type: MatchType
    match_score: Optional[float]
    bureaus_involved: Optional[List[str]]
    status: OverlapAlertStatus
    created_at: datetime
    updated_at: datetime
    match_reasons: Optional[List[str]] = None
    detection_method: Optional[str] = None
    similarity_score: Optional[float] = None

    model_config = {"from_attributes": True}


class OverlapAlertResponse(BaseModel):
    id: uuid.UUID
    alert_number: str
    case_id_incoming: uuid.UUID
    case_id_existing: uuid.UUID
    institution_id: Optional[uuid.UUID]
    match_type: MatchType
    match_score: Optional[float]
    match_evidence: Optional[Dict[str, Any]]
    bureaus_involved: Optional[List[str]]
    status: OverlapAlertStatus
    created_at: datetime
    updated_at: datetime
    match_reasons: Optional[List[str]] = None
    detection_method: Optional[str] = None
    similarity_score: Optional[float] = None
    # enriched comparison data
    incoming_case: Optional[RelatedCaseSummary] = None
    existing_case: Optional[RelatedCaseSummary] = None
    reviews: List["OverlapReviewResponse"] = []

    model_config = {"from_attributes": True}


# ── Review schemas ─────────────────────────────────────────────────────────────

class OverlapReviewCreate(BaseModel):
    decision: OverlapReviewDecision
    remarks: Optional[str] = None
    coordination_owner_id: Optional[uuid.UUID] = None


class OverlapReviewResponse(BaseModel):
    id: uuid.UUID
    alert_id: uuid.UUID
    reviewed_by_id: Optional[uuid.UUID]
    reviewed_at: datetime
    decision: OverlapReviewDecision
    remarks: Optional[str]
    coordination_owner_id: Optional[uuid.UUID]

    model_config = {"from_attributes": True}


# ── Pagination ─────────────────────────────────────────────────────────────────

class PaginatedOverlapAlerts(BaseModel):
    items: List[OverlapAlertListItem]
    total: int
    page: int
    page_size: int
    pages: int
