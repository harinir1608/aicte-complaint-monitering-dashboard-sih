from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, require_admin, require_role
from app.models.case import Case, CaseStatus
from app.models.overlap import OverlapAlert, OverlapAlertStatus
from app.models.user import User, UserRole
from app.schemas.institution import (
    InstitutionAliasCreate,
    InstitutionAliasResponse,
    InstitutionCreate,
    InstitutionListResponse,
    InstitutionProfile,
    InstitutionResponse,
    InstitutionUpdate,
    PaginatedInstitutions,
    BureauCaseSummary,
    InstitutionGraph,
)
from app.schemas.case import CaseListItem, PaginatedCases
from app.services import institution_service, case_service

router = APIRouter(prefix="/institutions", tags=["Institutions"])


@router.get("", response_model=PaginatedInstitutions)
def list_institutions(
    name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),          # alias for name
    permanent_id: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    region_id: Optional[uuid.UUID] = Query(None),
    institution_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    page_size: int = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # `search` is the frontend-friendly alias; `name` takes precedence if both given
    effective_name = name or search
    effective_page_size = page_size or size or 20
    items, total, pages = institution_service.list_institutions(
        db=db,
        name=effective_name,
        permanent_id=permanent_id,
        state=state,
        region_id=region_id,
        institution_type=institution_type,
        is_active=is_active,
        page=page,
        page_size=effective_page_size,
    )
    return PaginatedInstitutions(
        items=[InstitutionListResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=effective_page_size,
        pages=pages,
    )


@router.post("", response_model=InstitutionResponse, status_code=201)
def create_institution(
    data: InstitutionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.system_admin,
            UserRole.rb_officer,
            UserRole.pgrc_officer,
            UserRole.bureau_officer,
        )
    ),
):
    inst = institution_service.create_institution(data=data, db=db, actor=current_user)
    return InstitutionResponse.model_validate(inst)


@router.get("/search", response_model=List[InstitutionListResponse])
def search_institutions(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    results = institution_service.search_institutions(query=q, db=db, limit=limit)
    return [InstitutionListResponse.model_validate(i) for i in results]


@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(
    institution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    inst = institution_service.get_institution(institution_id, db)
    return InstitutionResponse.model_validate(inst)


@router.patch("/{institution_id}", response_model=InstitutionResponse)
def update_institution(
    institution_id: uuid.UUID,
    data: InstitutionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    inst = institution_service.update_institution(
        institution_id=institution_id, data=data, db=db, actor=current_user
    )
    return InstitutionResponse.model_validate(inst)


@router.get("/{institution_id}/profile")
def get_institution_profile(
    institution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return full institution profile with statistics, case history, and officer assignments."""
    profile_data = institution_service.get_institution_profile(institution_id, db)
    # Build response manually to avoid schema impedance
    inst_resp = InstitutionResponse.model_validate(profile_data["institution"])
    bureau_breakdown = [
        BureauCaseSummary(**b) for b in profile_data["bureau_breakdown"]
    ]
    return {
        **profile_data,
        "institution": inst_resp.model_dump(),
        "bureau_breakdown": [b.model_dump() for b in bureau_breakdown],
        # case_history and assigned_officers already serializable dicts
    }


@router.get("/{institution_id}/graph", response_model=InstitutionGraph)
def get_institution_graph(
    institution_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Return relationship graph data (nodes + edges) for an institution."""
    graph_data = institution_service.get_institution_graph(institution_id, db)
    return InstitutionGraph(**graph_data)


@router.get("/{institution_id}/cases", response_model=PaginatedCases)
def get_institution_cases(
    institution_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    # Verify institution exists
    institution_service.get_institution(institution_id, db)

    items, total, pages = case_service.list_cases(
        db=db,
        actor=current_user,
        institution_id=institution_id,
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


@router.post("/{institution_id}/aliases", response_model=InstitutionAliasResponse, status_code=201)
def add_alias(
    institution_id: uuid.UUID,
    data: InstitutionAliasCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    alias = institution_service.add_alias(
        institution_id=institution_id, alias_data=data, db=db, actor=current_user
    )
    return InstitutionAliasResponse.model_validate(alias)
