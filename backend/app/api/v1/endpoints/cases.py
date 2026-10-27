from __future__ import annotations

import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.case import RelationshipType
from app.models.user import User
from app.schemas.case import (
    CaseActionCreate,
    CaseActionResponse,
    CaseAssignmentCreate,
    CaseAssignmentResponse,
    CaseCreate,
    CaseDocumentResponse,
    CaseEscalateRequest,
    CaseListItem,
    CasePriority,
    CaseResponse,
    CaseStatusUpdate,
    CaseTransferRequest,
    CaseUpdate,
    PaginatedCases,
    RelatedCaseCreate,
    RelatedCaseResponse,
)
from app.services import case_service

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get("", response_model=PaginatedCases)
def list_cases(
    bureau_id: Optional[uuid.UUID] = Query(None),
    institution_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    search: Optional[str] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    items, total, pages = case_service.list_cases(
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
        is_overdue=is_overdue,
        page=page,
        page_size=page_size,
    )
    return PaginatedCases(
        items=[CaseListItem.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(
    data: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = case_service.create_case(data=data, db=db, actor=current_user)
    return CaseResponse.model_validate(case)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = case_service.get_case(case_id, db)
    return CaseResponse.model_validate(case)


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(
    case_id: uuid.UUID,
    data: CaseStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = case_service.update_case_status(
        case_id=case_id,
        new_status=data.new_status,
        remarks=data.remarks,
        db=db,
        actor=current_user,
    )
    return CaseResponse.model_validate(case)


@router.post("/{case_id}/assign", response_model=CaseAssignmentResponse, status_code=201)
def assign_case(
    case_id: uuid.UUID,
    data: CaseAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    assignment = case_service.assign_case(
        case_id=case_id,
        officer_id=data.officer_id,
        notes=data.notes,
        db=db,
        actor=current_user,
    )
    return CaseAssignmentResponse.model_validate(assignment)


@router.post("/{case_id}/transfer", response_model=CaseResponse)
def transfer_case(
    case_id: uuid.UUID,
    data: CaseTransferRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    case = case_service.transfer_case(
        case_id=case_id,
        target_bureau_id=data.target_bureau_id,
        reason=data.reason,
        db=db,
        actor=current_user,
    )
    return CaseResponse.model_validate(case)


@router.post("/{case_id}/actions", response_model=CaseActionResponse, status_code=201)
def add_case_action(
    case_id: uuid.UUID,
    data: CaseActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    action = case_service.add_case_action(
        case_id=case_id, action_data=data, db=db, actor=current_user
    )
    return CaseActionResponse.model_validate(action)


@router.get("/{case_id}/history", response_model=List[CaseActionResponse])
def get_case_history(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    actions = case_service.get_case_history(case_id, db)
    return [CaseActionResponse.model_validate(a) for a in actions]


@router.post("/{case_id}/related-cases", response_model=RelatedCaseResponse, status_code=201)
def link_related_case(
    case_id: uuid.UUID,
    data: RelatedCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    link = case_service.link_cases(
        case_id_1=case_id,
        case_id_2=data.related_case_id,
        relationship_type=data.relationship_type,
        rationale=data.rationale,
        db=db,
        actor=current_user,
    )
    return RelatedCaseResponse.model_validate(link)


@router.get("/{case_id}/related-cases", response_model=List[RelatedCaseResponse])
def get_related_cases(
    case_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    links = case_service.get_related_cases(case_id, db)
    return [RelatedCaseResponse.model_validate(l) for l in links]


@router.post("/{case_id}/documents", response_model=CaseDocumentResponse, status_code=201)
async def upload_case_document(
    case_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doc = await case_service.upload_case_document(
        case_id=case_id, file=file, db=db, actor=current_user
    )
    return CaseDocumentResponse.model_validate(doc)
