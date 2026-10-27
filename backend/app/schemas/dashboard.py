from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


# ── KPI summary ───────────────────────────────────────────────────────────────

class DashboardSummary(BaseModel):
    total_complaints: int
    total_cases: int
    active_cases: int
    pending_assignment: int
    under_process: int
    awaiting_information: int
    transferred: int
    escalated: int
    disposed: int
    closed: int
    overdue_cases: int
    cases_approaching_deadline: int = 0
    overlaps_pending_review: int
    overlaps_confirmed: int
    overlaps_false_positive: int
    conflict_warnings_unresolved: int = 0


# ── Trend data point ──────────────────────────────────────────────────────────

class TrendPoint(BaseModel):
    period: str          # e.g. "2024-01" (YYYY-MM)
    intake: int
    disposed: int
    active: int


# ── Workload entries ──────────────────────────────────────────────────────────

class WorkloadEntry(BaseModel):
    entity_id: uuid.UUID
    entity_name: str
    entity_type: str     # "bureau" | "officer"
    total_cases: int
    active_cases: int
    overdue_cases: int


# ── Overlap summary ────────────────────────────────────────────────────────────

class OverlapSummary(BaseModel):
    pending_review: int
    confirmed_related: int
    false_positive: int
    linked: int
    dismissed: int


# ── Institution table entry ────────────────────────────────────────────────────

class InstitutionTableEntry(BaseModel):
    institution_id: uuid.UUID
    institution_name: str
    permanent_id: Optional[str]
    total_complaints: int
    total_cases: int
    active_cases: int
    overdue_cases: int
    overlap_count: int
    latest_activity: Optional[datetime]


class PaginatedInstitutionTable(BaseModel):
    items: List[InstitutionTableEntry]
    total: int
    page: int
    page_size: int
    pages: int


# ── Ageing bucket ──────────────────────────────────────────────────────────────

class AgeingBucket(BaseModel):
    bucket: str      # e.g. "0-30 days", "31-60 days", etc.
    count: int
    percentage: float
