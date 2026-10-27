from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import (
    Case,
    CaseAction,
    CaseActionType,
    CaseAssignment,
    CaseDocument,
    CaseStatus,
    RelatedCase,
    RelationshipType,
)
from app.models.complaint import Complaint
from app.models.user import User, UserRole
from app.schemas.case import CaseActionCreate, CaseCreate, CaseUpdate, RelatedCaseCreate
from app.services.audit_service import log_action
from app.services.storage_service import get_storage_service, validate_upload

# ── Valid status transitions ───────────────────────────────────────────────────

VALID_TRANSITIONS: Dict[CaseStatus, List[CaseStatus]] = {
    CaseStatus.received: [CaseStatus.pending_assignment],
    CaseStatus.pending_assignment: [CaseStatus.under_process],
    CaseStatus.under_process: [
        CaseStatus.awaiting_information,
        CaseStatus.transferred,
        CaseStatus.escalated,
        CaseStatus.disposed,
    ],
    CaseStatus.awaiting_information: [CaseStatus.under_process, CaseStatus.disposed],
    CaseStatus.transferred: [CaseStatus.under_process, CaseStatus.disposed],
    CaseStatus.escalated: [CaseStatus.under_process, CaseStatus.disposed],
    CaseStatus.disposed: [CaseStatus.closed],
    CaseStatus.closed: [],
}


# ── Number generation ──────────────────────────────────────────────────────────

def generate_case_number(bureau_code: str, db: Session) -> str:
    """Generate a sequential case number like 'RB-2024-000001'."""
    year = datetime.now(timezone.utc).year
    prefix = f"{bureau_code.upper()}-{year}-"
    count = db.execute(
        select(func.count(Case.id)).where(Case.case_number.like(f"{prefix}%"))
    ).scalar_one()
    return f"{prefix}{count + 1:06d}"


# ── Helpers ────────────────────────────────────────────────────────────────────

def _get_or_404(case_id: uuid.UUID, db: Session) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case {case_id} not found",
        )
    return case


# ── CRUD ───────────────────────────────────────────────────────────────────────

def create_case_from_complaint(
    *,
    complaint_id: uuid.UUID,
    bureau_id: uuid.UUID,
    db: Session,
    actor: Optional[User] = None,
) -> Case:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")

    bureau = db.get(Bureau, bureau_id)
    if bureau is None:
        raise HTTPException(status_code=404, detail="Bureau not found")

    case_number = generate_case_number(bureau.code, db)
    case = Case(
        case_number=case_number,
        complaint_id=complaint_id,
        institution_id=complaint.institution_id,
        bureau_id=bureau_id,
        category_id=complaint.category_id,
        subject=complaint.subject,
        description=complaint.description,
        priority=complaint.priority,
        created_by_id=actor.id if actor else None,
    )
    db.add(case)
    db.flush()

    # Initial action
    action = CaseAction(
        case_id=case.id,
        action_type=CaseActionType.note,
        description=f"Case created from complaint {complaint.complaint_number}",
        performed_by_id=actor.id if actor else None,
        old_status=None,
        new_status=CaseStatus.received,
    )
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case.id,
        action="created",
        actor=actor,
        new_val={"case_number": case_number, "complaint_id": str(complaint_id)},
        db=db,
    )
    db.commit()
    db.refresh(case)
    return case


def create_case(
    *,
    data: CaseCreate,
    db: Session,
    actor: Optional[User] = None,
) -> Case:
    bureau_code = "AICTE"
    if data.bureau_id:
        bureau = db.get(Bureau, data.bureau_id)
        if bureau:
            bureau_code = bureau.code

    case_number = generate_case_number(bureau_code, db)
    case = Case(
        **data.model_dump(),
        case_number=case_number,
        created_by_id=actor.id if actor else None,
    )
    db.add(case)
    db.flush()

    action = CaseAction(
        case_id=case.id,
        action_type=CaseActionType.note,
        description="Case created",
        performed_by_id=actor.id if actor else None,
        new_status=CaseStatus.received,
    )
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case.id,
        action="created",
        actor=actor,
        new_val={"case_number": case_number},
        db=db,
    )
    db.commit()
    db.refresh(case)
    return case


def update_case_status(
    *,
    case_id: uuid.UUID,
    new_status: CaseStatus,
    remarks: Optional[str],
    db: Session,
    actor: Optional[User] = None,
) -> Case:
    case = _get_or_404(case_id, db)
    old_status = case.status

    allowed = VALID_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid status transition from '{old_status}' to '{new_status}'. "
                f"Allowed: {[s.value for s in allowed]}"
            ),
        )

    case.status = new_status
    if new_status == CaseStatus.disposed and not case.disposal_date:
        case.disposal_date = datetime.now(timezone.utc).date()
        if remarks:
            case.disposal_remarks = remarks

    action = CaseAction(
        case_id=case.id,
        action_type=CaseActionType.status_change,
        description=remarks or f"Status changed to {new_status}",
        performed_by_id=actor.id if actor else None,
        old_status=old_status.value,
        new_status=new_status.value,
    )
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case.id,
        action="status_changed",
        actor=actor,
        old_val={"status": old_status.value},
        new_val={"status": new_status.value},
        remarks=remarks,
        db=db,
    )
    db.commit()
    db.refresh(case)
    return case


def assign_case(
    *,
    case_id: uuid.UUID,
    officer_id: uuid.UUID,
    notes: Optional[str],
    db: Session,
    actor: Optional[User] = None,
) -> CaseAssignment:
    case = _get_or_404(case_id, db)

    # Mark existing assignments as not current
    for existing in case.assignments:
        existing.is_current = False

    assignment = CaseAssignment(
        case_id=case_id,
        assigned_to_id=officer_id,
        assigned_by_id=actor.id if actor else None,
        notes=notes,
        is_current=True,
    )
    db.add(assignment)
    db.flush()

    action = CaseAction(
        case_id=case_id,
        action_type=CaseActionType.assignment,
        description=f"Case assigned to officer {officer_id}. Notes: {notes or 'None'}",
        performed_by_id=actor.id if actor else None,
    )
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case_id,
        action="assigned",
        actor=actor,
        new_val={"officer_id": str(officer_id), "notes": notes},
        db=db,
    )
    db.commit()
    db.refresh(assignment)
    return assignment


def transfer_case(
    *,
    case_id: uuid.UUID,
    target_bureau_id: uuid.UUID,
    reason: str,
    db: Session,
    actor: Optional[User] = None,
) -> Case:
    case = _get_or_404(case_id, db)
    old_bureau_id = case.bureau_id
    case.bureau_id = target_bureau_id

    action = CaseAction(
        case_id=case_id,
        action_type=CaseActionType.transfer,
        description=f"Case transferred. Reason: {reason}",
        performed_by_id=actor.id if actor else None,
        old_status=case.status.value,
        new_status=CaseStatus.transferred.value,
        metadata_={"old_bureau_id": str(old_bureau_id), "new_bureau_id": str(target_bureau_id)},
    )
    case.status = CaseStatus.transferred
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case_id,
        action="transferred",
        actor=actor,
        old_val={"bureau_id": str(old_bureau_id)},
        new_val={"bureau_id": str(target_bureau_id)},
        remarks=reason,
        db=db,
    )
    db.commit()
    db.refresh(case)
    return case


def add_case_action(
    *,
    case_id: uuid.UUID,
    action_data: CaseActionCreate,
    db: Session,
    actor: Optional[User] = None,
) -> CaseAction:
    _get_or_404(case_id, db)

    action = CaseAction(
        case_id=case_id,
        action_type=action_data.action_type,
        description=action_data.description,
        performed_by_id=actor.id if actor else None,
    )
    db.add(action)
    db.flush()

    log_action(
        entity_type="case",
        entity_id=case_id,
        action="action_added",
        actor=actor,
        new_val={"action_type": action_data.action_type, "description": action_data.description},
        db=db,
    )
    db.commit()
    db.refresh(action)
    return action


def get_case(case_id: uuid.UUID, db: Session) -> Case:
    return _get_or_404(case_id, db)


def list_cases(
    *,
    db: Session,
    actor: Optional[User] = None,
    bureau_id: Optional[uuid.UUID] = None,
    institution_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category_id: Optional[uuid.UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Case], int, int]:
    stmt = select(Case)

    # Bureau-based filtering for non-admin users
    if actor and actor.role not in (UserRole.system_admin, UserRole.senior_management):
        if actor.bureau_id:
            stmt = stmt.where(Case.bureau_id == actor.bureau_id)

    if bureau_id:
        stmt = stmt.where(Case.bureau_id == bureau_id)
    if institution_id:
        stmt = stmt.where(Case.institution_id == institution_id)
    if status:
        stmt = stmt.where(Case.status == status)
    if priority:
        stmt = stmt.where(Case.priority == priority)
    if category_id:
        stmt = stmt.where(Case.category_id == category_id)
    if date_from:
        stmt = stmt.where(Case.created_at >= date_from)
    if date_to:
        stmt = stmt.where(Case.created_at <= date_to)
    if search:
        stmt = stmt.where(Case.subject.ilike(f"%{search}%"))
    if is_overdue:
        today = datetime.now(timezone.utc).date()
        stmt = stmt.where(
            Case.expected_disposal_date < today,
            Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
        )

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = db.execute(
        stmt.order_by(Case.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    return list(items), total, pages


def get_case_history(case_id: uuid.UUID, db: Session) -> List[CaseAction]:
    _get_or_404(case_id, db)
    stmt = (
        select(CaseAction)
        .where(CaseAction.case_id == case_id)
        .order_by(CaseAction.performed_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def link_cases(
    *,
    case_id_1: uuid.UUID,
    case_id_2: uuid.UUID,
    relationship_type: RelationshipType,
    rationale: Optional[str],
    db: Session,
    actor: Optional[User] = None,
) -> RelatedCase:
    _get_or_404(case_id_1, db)
    _get_or_404(case_id_2, db)

    # Prevent duplicate links
    existing = db.execute(
        select(RelatedCase).where(
            or_(
                (RelatedCase.case_id_1 == case_id_1) & (RelatedCase.case_id_2 == case_id_2),
                (RelatedCase.case_id_1 == case_id_2) & (RelatedCase.case_id_2 == case_id_1),
            )
        )
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="These cases are already linked.",
        )

    link = RelatedCase(
        case_id_1=case_id_1,
        case_id_2=case_id_2,
        relationship_type=relationship_type,
        rationale=rationale,
        linked_by_id=actor.id if actor else None,
    )
    db.add(link)
    db.flush()

    log_action(
        entity_type="case",
        entity_id=case_id_1,
        action="cases_linked",
        actor=actor,
        new_val={
            "related_case_id": str(case_id_2),
            "relationship_type": relationship_type,
        },
        db=db,
    )
    db.commit()
    db.refresh(link)
    return link


def get_related_cases(case_id: uuid.UUID, db: Session) -> List[RelatedCase]:
    stmt = select(RelatedCase).where(
        or_(RelatedCase.case_id_1 == case_id, RelatedCase.case_id_2 == case_id)
    )
    return list(db.execute(stmt).scalars().all())


async def upload_case_document(
    *,
    case_id: uuid.UUID,
    file: UploadFile,
    db: Session,
    actor: Optional[User] = None,
) -> CaseDocument:
    _get_or_404(case_id, db)
    validate_upload(file)

    file_data = await file.read()
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the 10 MB size limit.",
        )

    storage = get_storage_service()
    storage_key = storage.upload_file(file_data, file.filename or "upload", file.content_type)

    doc = CaseDocument(
        case_id=case_id,
        filename=file.filename or "upload",
        storage_key=storage_key,
        file_size=len(file_data),
        content_type=file.content_type,
        uploaded_by_id=actor.id if actor else None,
    )
    db.add(doc)
    db.flush()

    # Record action
    action = CaseAction(
        case_id=case_id,
        action_type=CaseActionType.document_upload,
        description=f"Document uploaded: {doc.filename}",
        performed_by_id=actor.id if actor else None,
    )
    db.add(action)

    log_action(
        entity_type="case",
        entity_id=case_id,
        action="document_uploaded",
        actor=actor,
        new_val={"filename": doc.filename, "storage_key": storage_key},
        db=db,
    )
    db.commit()
    db.refresh(doc)
    return doc
