from __future__ import annotations

import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintDocumentResponse,
    ComplaintListItem,
    ComplaintResponse,
    ComplaintUpdate,
    PaginatedComplaints,
)
from app.schemas.case import CaseResponse
from app.services import complaint_service, case_service

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.get("", response_model=PaginatedComplaints)
def list_complaints(
    bureau_id: Optional[uuid.UUID] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total, pages = complaint_service.list_complaints(
        db=db,
        actor=current_user,
        bureau_id=bureau_id,
        institution_id=institution_id,
        status=status,
        priority=priority,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PaginatedComplaints(
        items=[ComplaintListItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=ComplaintResponse, status_code=201)
def create_complaint(
    data: ComplaintCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    complaint = complaint_service.create_complaint(data=data, db=db, actor=current_user)
    return ComplaintResponse.model_validate(complaint)


@router.get("/{complaint_id}", response_model=ComplaintResponse)
def get_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    complaint = complaint_service.get_complaint(complaint_id, db)
    return ComplaintResponse.model_validate(complaint)


@router.patch("/{complaint_id}", response_model=ComplaintResponse)
def update_complaint(
    complaint_id: uuid.UUID,
    data: ComplaintUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    complaint = complaint_service.update_complaint(
        complaint_id=complaint_id, data=data, db=db, actor=current_user
    )
    return ComplaintResponse.model_validate(complaint)


@router.post("/{complaint_id}/documents", response_model=ComplaintDocumentResponse, status_code=201)
async def upload_document(
    complaint_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doc = await complaint_service.upload_document(
        complaint_id=complaint_id, file=file, db=db, actor=current_user
    )
    return ComplaintDocumentResponse.model_validate(doc)


@router.post("/{complaint_id}/create-case", response_model=CaseResponse, status_code=201)
def create_case_from_complaint(
    complaint_id: uuid.UUID,
    bureau_id: uuid.UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = case_service.create_case_from_complaint(
        complaint_id=complaint_id,
        bureau_id=bureau_id,
        db=db,
        actor=current_user,
    )
    return CaseResponse.model_validate(case)
