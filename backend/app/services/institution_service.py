from __future__ import annotations

import math
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.institution import Institution, InstitutionAlias
from app.models.user import User
from app.schemas.institution import (
    InstitutionAliasCreate,
    InstitutionCreate,
    InstitutionUpdate,
)
from app.services.audit_service import log_action


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_or_404(institution_id: uuid.UUID, db: Session) -> Institution:
    inst = db.get(Institution, institution_id)
    if inst is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Institution {institution_id} not found",
        )
    return inst


# ── CRUD ───────────────────────────────────────────────────────────────────────

def create_institution(
    *,
    data: InstitutionCreate,
    db: Session,
    actor: Optional[User] = None,
) -> Institution:
    # Duplicate permanent_id check
    if data.permanent_id:
        existing = db.execute(
            select(Institution).where(Institution.permanent_id == data.permanent_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An institution with permanent_id '{data.permanent_id}' already exists.",
            )

    inst = Institution(
        **data.model_dump(),
        created_by_id=actor.id if actor else None,
    )
    db.add(inst)
    db.flush()

    log_action(
        entity_type="institution",
        entity_id=inst.id,
        action="created",
        actor=actor,
        new_val={"name": inst.name, "permanent_id": inst.permanent_id},
        db=db,
    )
    db.commit()
    db.refresh(inst)
    return inst


def update_institution(
    *,
    institution_id: uuid.UUID,
    data: InstitutionUpdate,
    db: Session,
    actor: Optional[User] = None,
) -> Institution:
    inst = _get_or_404(institution_id, db)

    # Duplicate permanent_id check on update
    if data.permanent_id and data.permanent_id != inst.permanent_id:
        conflict = db.execute(
            select(Institution).where(
                Institution.permanent_id == data.permanent_id,
                Institution.id != institution_id,
            )
        ).scalar_one_or_none()
        if conflict:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An institution with permanent_id '{data.permanent_id}' already exists.",
            )

    old_vals = {k: str(getattr(inst, k)) for k in data.model_fields_set}
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(inst, field, value)

    log_action(
        entity_type="institution",
        entity_id=inst.id,
        action="updated",
        actor=actor,
        old_val=old_vals,
        new_val=data.model_dump(exclude_unset=True),
        db=db,
    )
    db.commit()
    db.refresh(inst)
    return inst


def get_institution(institution_id: uuid.UUID, db: Session) -> Institution:
    return _get_or_404(institution_id, db)


def list_institutions(
    *,
    db: Session,
    name: Optional[str] = None,
    permanent_id: Optional[str] = None,
    state: Optional[str] = None,
    region_id: Optional[uuid.UUID] = None,
    institution_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
):
    from sqlalchemy import or_
    stmt = select(Institution)

    if name:
        # Search across name AND permanent_id simultaneously
        stmt = stmt.where(
            or_(
                Institution.name.ilike(f"%{name}%"),
                Institution.permanent_id.ilike(f"%{name}%"),
            )
        )
    if permanent_id:
        stmt = stmt.where(Institution.permanent_id.ilike(f"%{permanent_id}%"))
    if state:
        stmt = stmt.where(Institution.state.ilike(f"%{state}%"))
    if region_id:
        stmt = stmt.where(Institution.region_id == region_id)
    if institution_type:
        stmt = stmt.where(Institution.institution_type == institution_type)
    if is_active is not None:
        stmt = stmt.where(Institution.is_active == is_active)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = db.execute(
        stmt.order_by(Institution.name).offset(offset).limit(page_size)
    ).scalars().all()

    return items, total, pages


def get_institution_profile(institution_id: uuid.UUID, db: Session) -> dict:
    """Return full institution profile including statistics and case history."""
    from datetime import date, timezone
    from sqlalchemy import func, select
    from app.models.case import Case, CaseStatus, CaseAssignment
    from app.models.complaint import Complaint
    from app.models.overlap import OverlapAlert, OverlapAlertStatus
    from app.models.bureau import Bureau

    inst = _get_or_404(institution_id, db)
    today = date.today()

    active_statuses = [
        CaseStatus.received,
        CaseStatus.pending_assignment,
        CaseStatus.under_process,
        CaseStatus.awaiting_information,
        CaseStatus.transferred,
        CaseStatus.escalated,
    ]

    def _count_cases(*statuses):
        q = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == institution_id,
                *(Case.status.in_(list(statuses)),) if statuses else (),
            )
        ).scalar_one()
        return q

    total_complaints = db.execute(
        select(func.count(Complaint.id)).where(Complaint.institution_id == institution_id)
    ).scalar_one()

    total_cases = db.execute(
        select(func.count(Case.id)).where(Case.institution_id == institution_id)
    ).scalar_one()

    active_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status.in_(active_statuses),
        )
    ).scalar_one()

    pending_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status == CaseStatus.pending_assignment,
        )
    ).scalar_one()

    under_process_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status == CaseStatus.under_process,
        )
    ).scalar_one()

    disposed_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status.in_([CaseStatus.disposed, CaseStatus.closed]),
        )
    ).scalar_one()

    transferred_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status == CaseStatus.transferred,
        )
    ).scalar_one()

    escalated_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.status == CaseStatus.escalated,
        )
    ).scalar_one()

    overdue_cases = db.execute(
        select(func.count(Case.id)).where(
            Case.institution_id == institution_id,
            Case.expected_disposal_date < today,
            Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
        )
    ).scalar_one()

    unresolved_overlap_alerts = db.execute(
        select(func.count(OverlapAlert.id)).where(
            OverlapAlert.institution_id == institution_id,
            OverlapAlert.status == OverlapAlertStatus.pending_review,
        )
    ).scalar_one()

    # Bureau breakdown
    bureaus = db.execute(select(Bureau).where(Bureau.is_active == True)).scalars().all()  # noqa: E712
    bureau_breakdown = []
    for bureau in bureaus:
        bc_total = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == institution_id,
                Case.bureau_id == bureau.id,
            )
        ).scalar_one()
        if bc_total == 0:
            continue
        bc_active = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == institution_id,
                Case.bureau_id == bureau.id,
                Case.status.in_(active_statuses),
            )
        ).scalar_one()
        bc_disposed = db.execute(
            select(func.count(Case.id)).where(
                Case.institution_id == institution_id,
                Case.bureau_id == bureau.id,
                Case.status.in_([CaseStatus.disposed, CaseStatus.closed]),
            )
        ).scalar_one()
        bureau_breakdown.append({
            "bureau_id": bureau.id,
            "bureau_name": bureau.name,
            "bureau_code": bureau.code,
            "total_cases": bc_total,
            "active_cases": bc_active,
            "disposed_cases": bc_disposed,
        })

    # Assigned officers (current assignments on active cases)
    assignment_rows = db.execute(
        select(CaseAssignment, Case)
        .join(Case, CaseAssignment.case_id == Case.id)
        .where(
            Case.institution_id == institution_id,
            CaseAssignment.is_current == True,  # noqa: E712
        )
    ).all()

    officer_map: dict = {}
    for assignment, case in assignment_rows:
        officer = assignment.assigned_to
        if not officer:
            continue
        oid = str(officer.id)
        if oid not in officer_map:
            bureau_name = None
            if officer.bureau_id:
                b = db.get(Bureau, officer.bureau_id)
                bureau_name = b.name if b else None
            officer_map[oid] = {
                "officer_id": officer.id,
                "officer_name": officer.full_name,
                "officer_email": officer.email,
                "bureau_name": bureau_name,
                "case_ids": [],
            }
        officer_map[oid]["case_ids"].append(case.id)

    assigned_officers = list(officer_map.values())

    # Case history (all cases, chronological)
    all_cases = db.execute(
        select(Case).where(Case.institution_id == institution_id).order_by(Case.created_at.desc())
    ).scalars().all()

    case_history = []
    for c in all_cases:
        bureau_name = None
        if c.bureau_id:
            b = db.get(Bureau, c.bureau_id)
            bureau_name = b.name if b else None
        case_history.append({
            "id": c.id,
            "case_number": c.case_number,
            "subject": c.subject,
            "status": c.status.value if c.status else None,
            "priority": c.priority.value if c.priority else None,
            "bureau_name": bureau_name,
            "expected_disposal_date": (
                c.expected_disposal_date.isoformat() if c.expected_disposal_date else None
            ),
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        })

    # Latest activity
    latest_row = db.execute(
        select(func.max(Case.updated_at)).where(Case.institution_id == institution_id)
    ).scalar_one()

    return {
        "institution": inst,
        "total_complaints": total_complaints,
        "total_cases": total_cases,
        "active_cases": active_cases,
        "pending_cases": pending_cases,
        "under_process_cases": under_process_cases,
        "disposed_cases": disposed_cases,
        "transferred_cases": transferred_cases,
        "escalated_cases": escalated_cases,
        "overdue_cases": overdue_cases,
        "unresolved_overlap_alerts": unresolved_overlap_alerts,
        "bureau_breakdown": bureau_breakdown,
        "assigned_officers": assigned_officers,
        "case_history": case_history,
        "latest_activity": latest_row,
    }


def get_institution_graph(institution_id: uuid.UUID, db: Session) -> dict:
    """Return nodes and edges for the institution relationship graph."""
    from sqlalchemy import select
    from app.models.case import Case, CaseAssignment
    from app.models.complaint import Complaint
    from app.models.bureau import Bureau

    inst = _get_or_404(institution_id, db)

    nodes = []
    edges = []
    seen_nodes: set[str] = set()

    def add_node(node_id: str, node_type: str, label: str, status: str | None = None, url: str | None = None, data: dict | None = None) -> None:
        if node_id not in seen_nodes:
            seen_nodes.add(node_id)
            nodes.append({
                "id": node_id,
                "node_type": node_type,
                "label": label,
                "status": status,
                "url": url,
                "data": data or {},
            })

    inst_node_id = f"inst-{inst.id}"
    add_node(inst_node_id, "institution", inst.name, url=f"/institutions/{inst.id}")

    # Complaints
    complaints = db.execute(
        select(Complaint).where(Complaint.institution_id == institution_id)
    ).scalars().all()
    for comp in complaints:
        c_id = f"complaint-{comp.id}"
        add_node(c_id, "complaint", comp.complaint_number, status=comp.status.value, url=f"/complaints/{comp.id}")
        edges.append({"id": f"e-{c_id}-{inst_node_id}", "source": c_id, "target": inst_node_id, "label": "filed at"})

    # Cases
    cases = db.execute(
        select(Case).where(Case.institution_id == institution_id)
    ).scalars().all()
    seen_bureaus: set[str] = set()
    for case in cases:
        case_id = f"case-{case.id}"
        add_node(case_id, "case", case.case_number, status=case.status.value, url=f"/cases/{case.id}")
        if case.complaint_id:
            comp_node_id = f"complaint-{case.complaint_id}"
            edges.append({"id": f"e-{case_id}-{comp_node_id}", "source": case_id, "target": comp_node_id, "label": "from complaint"})
        else:
            edges.append({"id": f"e-{case_id}-{inst_node_id}", "source": case_id, "target": inst_node_id, "label": "for institution"})
        if case.bureau_id:
            bureau_node_id = f"bureau-{case.bureau_id}"
            if case.bureau_id not in seen_bureaus:
                seen_bureaus.add(str(case.bureau_id))
                bureau = db.get(Bureau, case.bureau_id)
                if bureau:
                    add_node(bureau_node_id, "bureau", bureau.name, url=None)
            edges.append({"id": f"e-{case_id}-{bureau_node_id}", "source": case_id, "target": bureau_node_id, "label": "assigned to"})

    return {"nodes": nodes, "edges": edges}


def search_institutions(query: str, db: Session, limit: int = 10) -> List[Institution]:
    """Quick search by name or permanent_id — used for dropdown/autocomplete."""
    stmt = (
        select(Institution)
        .where(
            Institution.is_active == True,
            or_(
                Institution.name.ilike(f"%{query}%"),
                Institution.permanent_id.ilike(f"%{query}%"),
            ),
        )
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def add_alias(
    *,
    institution_id: uuid.UUID,
    alias_data: InstitutionAliasCreate,
    db: Session,
    actor: Optional[User] = None,
) -> InstitutionAlias:
    _get_or_404(institution_id, db)  # ensure institution exists

    alias = InstitutionAlias(
        institution_id=institution_id,
        **alias_data.model_dump(),
    )
    db.add(alias)
    db.flush()

    log_action(
        entity_type="institution_alias",
        entity_id=alias.id,
        action="alias_added",
        actor=actor,
        new_val={"institution_id": str(institution_id), "alias": alias.alias},
        db=db,
    )
    db.commit()
    db.refresh(alias)
    return alias
