from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.complaint import ComplaintSource, ComplaintStatus, ComplaintPriority


# ── Category schemas ──────────────────────────────────────────────────────────

class ComplaintCategoryCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    default_sla_days: Optional[int] = Field(None, ge=1)


class ComplaintCategoryResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    default_sla_days: Optional[int]

    model_config = {"from_attributes": True}


# ── Document schemas ──────────────────────────────────────────────────────────

class ComplaintDocumentResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    filename: str
    storage_key: str
    file_size: Optional[int]
    content_type: Optional[str]
    uploaded_by_id: Optional[uuid.UUID]
    uploaded_at: datetime

    model_config = {"from_attributes": True}


# ── Complaint CRUD schemas ─────────────────────────────────────────────────────

class ComplaintCreate(BaseModel):
    institution_id: Optional[uuid.UUID] = None
    institution_name_raw: Optional[str] = None
    source: ComplaintSource = ComplaintSource.other
    category_id: Optional[uuid.UUID] = None
    subject: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    received_date: date
    complainant_name: Optional[str] = Field(None, max_length=200)
    complainant_contact: Optional[str] = Field(None, max_length=200)
    is_anonymous: bool = False
    bureau_id: Optional[uuid.UUID] = None
    priority: ComplaintPriority = ComplaintPriority.normal


class ComplaintUpdate(BaseModel):
    institution_id: Optional[uuid.UUID] = None
    institution_name_raw: Optional[str] = None
    source: Optional[ComplaintSource] = None
    category_id: Optional[uuid.UUID] = None
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    received_date: Optional[date] = None
    complainant_name: Optional[str] = Field(None, max_length=200)
    complainant_contact: Optional[str] = Field(None, max_length=200)
    is_anonymous: Optional[bool] = None
    bureau_id: Optional[uuid.UUID] = None
    priority: Optional[ComplaintPriority] = None
    status: Optional[ComplaintStatus] = None


class ComplaintResponse(BaseModel):
    id: uuid.UUID
    complaint_number: str
    institution_id: Optional[uuid.UUID]
    institution_name_raw: Optional[str]
    source: ComplaintSource
    category_id: Optional[uuid.UUID]
    subject: str
    description: Optional[str]
    received_date: date
    complainant_name: Optional[str]
    complainant_contact: Optional[str]
    is_anonymous: bool
    bureau_id: Optional[uuid.UUID]
    status: ComplaintStatus
    priority: ComplaintPriority
    created_by_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime
    documents: List[ComplaintDocumentResponse] = []

    model_config = {"from_attributes": True}


class ComplaintListItem(BaseModel):
    id: uuid.UUID
    complaint_number: str
    institution_id: Optional[uuid.UUID]
    institution_name_raw: Optional[str]
    subject: str
    source: ComplaintSource
    status: ComplaintStatus
    priority: ComplaintPriority
    received_date: date
    bureau_id: Optional[uuid.UUID]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Pagination wrapper ─────────────────────────────────────────────────────────

class PaginatedComplaints(BaseModel):
    items: List[ComplaintListItem]
    total: int
    page: int
    page_size: int
    pages: int
