from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


# ── Filters ────────────────────────────────────────────────────────────────────

class ReportFilters(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    bureau_id: Optional[uuid.UUID] = None
    region_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    status: Optional[str] = None
    priority: Optional[str] = None


# ── Institution report ─────────────────────────────────────────────────────────

class InstitutionReportRow(BaseModel):
    institution_id: uuid.UUID
    institution_name: str
    permanent_id: Optional[str]
    state: Optional[str]
    region_name: Optional[str]
    total_complaints: int
    total_cases: int
    active_cases: int
    disposed_cases: int
    overdue_cases: int
    overlap_count: int
    latest_activity: Optional[datetime]


class InstitutionReport(BaseModel):
    filters: ReportFilters
    generated_at: datetime
    rows: List[InstitutionReportRow]
    total_rows: int


# ── Ageing report ─────────────────────────────────────────────────────────────

class AgeingReportRow(BaseModel):
    case_id: uuid.UUID
    case_number: str
    institution_name: Optional[str]
    bureau_name: Optional[str]
    subject: str
    status: str
    priority: str
    created_at: datetime
    expected_disposal_date: Optional[date]
    age_days: int
    is_overdue: bool


class AgeingReport(BaseModel):
    filters: ReportFilters
    generated_at: datetime
    rows: List[AgeingReportRow]
    total_rows: int
    overdue_count: int


# ── Workload report ────────────────────────────────────────────────────────────

class WorkloadReportRow(BaseModel):
    entity_type: str   # "bureau" | "officer"
    entity_name: str
    total_cases: int
    active_cases: int
    disposed_cases: int
    overdue_cases: int
    average_age_days: Optional[float]


class WorkloadReport(BaseModel):
    filters: ReportFilters
    generated_at: datetime
    rows: List[WorkloadReportRow]
    total_rows: int


# ── Overlap report ─────────────────────────────────────────────────────────────

class OverlapReportRow(BaseModel):
    alert_id: uuid.UUID
    alert_number: str
    incoming_case_number: str
    existing_case_number: str
    institution_name: Optional[str]
    match_type: str
    match_score: Optional[float]
    alert_status: str
    review_decision: Optional[str]
    reviewed_at: Optional[datetime]
    created_at: datetime


class OverlapReport(BaseModel):
    filters: ReportFilters
    generated_at: datetime
    rows: List[OverlapReportRow]
    total_rows: int
