from __future__ import annotations

import math
import uuid
from datetime import date, datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.complaint import Complaint, ComplaintDocument, ComplaintStatus
from app.models.user import User, UserRole
from app.schemas.complaint import ComplaintCreate, ComplaintUpdate
from app.services.audit_service import log_action
from app.services.storage_service import get_storage_service, validate_upload


# ── Number generation ──────────────────────────────────────────────────────────

def generate_complaint_number(bureau_code: str, db: Session) -> str:
    """Generate a sequential complaint number like 'PGRC-2024-000001'."""
    year = datetime.now(timezone.utc).year
    prefix = f"{bureau_code.upper()}-{year}-"

    # Count existing complaints with this prefix
    count = db.execute(
        select(func.count(Complaint.id)).where(
            Complaint.complaint_number.like(f"{prefix}%")
        )
    ).scalar_one()

    return f"{prefix}{count + 1:06d}"


# ── CRUD ───────────────────────────────────────────────────────────────────────

def _get_or_404(complaint_id: uuid.UUID, db: Session) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint {complaint_id} not found",
        )
    return complaint


def create_complaint(
    *,
    data: ComplaintCreate,
    db: Session,
    actor: Optional[User] = None,
) -> Complaint:
    # Determine bureau code for complaint number
    bureau_code = "AICTE"
    if data.bureau_id:
        bureau = db.get(Bureau, data.bureau_id)
        if bureau:
            bureau_code = bureau.code

    complaint_number = generate_complaint_number(bureau_code, db)

    complaint = Complaint(
        **data.model_dump(),
        complaint_number=complaint_number,
        created_by_id=actor.id if actor else None,
    )
    db.add(complaint)
    db.flush()

    log_action(
        entity_type="complaint",
        entity_id=complaint.id,
        action="created",
        actor=actor,
        new_val={
            "complaint_number": complaint_number,
            "subject": complaint.subject,
            "bureau_id": str(complaint.bureau_id) if complaint.bureau_id else None,
        },
        db=db,
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def update_complaint(
    *,
    complaint_id: uuid.UUID,
    data: ComplaintUpdate,
    db: Session,
    actor: Optional[User] = None,
) -> Complaint:
    complaint = _get_or_404(complaint_id, db)
    old_vals = {k: str(getattr(complaint, k, None)) for k in data.model_fields_set}

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(complaint, field, value)

    log_action(
        entity_type="complaint",
        entity_id=complaint.id,
        action="updated",
        actor=actor,
        old_val=old_vals,
        new_val=data.model_dump(exclude_unset=True),
        db=db,
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def get_complaint(complaint_id: uuid.UUID, db: Session) -> Complaint:
    return _get_or_404(complaint_id, db)


def list_complaints(
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
    page: int = 1,
    page_size: int = 20,
) -> Tuple[List[Complaint], int, int]:
    stmt = select(Complaint)

    # Bureau-based filtering for non-admin users
    if actor and actor.role not in (UserRole.system_admin, UserRole.senior_management):
        if actor.bureau_id:
            stmt = stmt.where(Complaint.bureau_id == actor.bureau_id)

    if bureau_id:
        stmt = stmt.where(Complaint.bureau_id == bureau_id)
    if institution_id:
        stmt = stmt.where(Complaint.institution_id == institution_id)
    if status:
        stmt = stmt.where(Complaint.status == status)
    if priority:
        stmt = stmt.where(Complaint.priority == priority)
    if category_id:
        stmt = stmt.where(Complaint.category_id == category_id)
    if date_from:
        stmt = stmt.where(Complaint.received_date >= date_from)
    if date_to:
        stmt = stmt.where(Complaint.received_date <= date_to)
    if search:
        stmt = stmt.where(Complaint.subject.ilike(f"%{search}%"))

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = db.execute(
        stmt.order_by(Complaint.created_at.desc()).offset(offset).limit(page_size)
    ).scalars().all()

    return list(items), total, pages


async def upload_document(
    *,
    complaint_id: uuid.UUID,
    file: UploadFile,
    db: Session,
    actor: Optional[User] = None,
) -> ComplaintDocument:
    _get_or_404(complaint_id, db)
    validate_upload(file)

    file_data = await file.read()
    if len(file_data) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds the 10 MB size limit.",
        )

    storage = get_storage_service()
    storage_key = storage.upload_file(file_data, file.filename or "upload", file.content_type)

    doc = ComplaintDocument(
        complaint_id=complaint_id,
        filename=file.filename or "upload",
        storage_key=storage_key,
        file_size=len(file_data),
        content_type=file.content_type,
        uploaded_by_id=actor.id if actor else None,
    )
    db.add(doc)
    db.flush()

    log_action(
        entity_type="complaint",
        entity_id=complaint_id,
        action="document_uploaded",
        actor=actor,
        new_val={"filename": doc.filename, "storage_key": storage_key},
        db=db,
    )
    db.commit()
    db.refresh(doc)
    return doc
