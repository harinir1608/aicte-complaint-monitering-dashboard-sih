from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_active_user, require_admin
from app.models.bureau import Bureau, Region
from app.models.user import User
from app.services.audit_service import log_action


# ── Pydantic schemas ────────────────────────────────────────────────────────

class BureauCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: bool = True


class BureauUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BureauResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class RegionCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    states: Optional[List[str]] = None
    is_active: bool = True


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    states: Optional[List[str]] = None
    is_active: Optional[bool] = None


class RegionResponse(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    description: Optional[str]
    states: Optional[List[str]]
    is_active: bool

    model_config = {"from_attributes": True}


# ── Routers ──────────────────────────────────────────────────────────────────

bureaus_router = APIRouter(prefix="/bureaus", tags=["Bureaus"])
regions_router = APIRouter(prefix="/regions", tags=["Regions"])


@bureaus_router.get("", response_model=List[BureauResponse])
def list_bureaus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    bureaus = db.execute(select(Bureau).order_by(Bureau.name)).scalars().all()
    return [BureauResponse.model_validate(b) for b in bureaus]


@bureaus_router.post("", response_model=BureauResponse, status_code=201)
def create_bureau(
    data: BureauCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.execute(select(Bureau).where(Bureau.code == data.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Bureau with code '{data.code}' already exists.")
    bureau = Bureau(**data.model_dump())
    db.add(bureau)
    db.flush()
    log_action(entity_type="bureau", entity_id=bureau.id, action="created",
               actor=current_user, new_val=data.model_dump(), db=db)
    db.commit()
    db.refresh(bureau)
    return BureauResponse.model_validate(bureau)


@bureaus_router.patch("/{bureau_id}", response_model=BureauResponse)
def update_bureau(
    bureau_id: uuid.UUID,
    data: BureauUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    bureau = db.get(Bureau, bureau_id)
    if not bureau:
        raise HTTPException(status_code=404, detail="Bureau not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bureau, field, value)
    log_action(entity_type="bureau", entity_id=bureau.id, action="updated",
               actor=current_user, new_val=data.model_dump(exclude_unset=True), db=db)
    db.commit()
    db.refresh(bureau)
    return BureauResponse.model_validate(bureau)


@regions_router.get("", response_model=List[RegionResponse])
def list_regions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    regions = db.execute(select(Region).order_by(Region.name)).scalars().all()
    return [RegionResponse.model_validate(r) for r in regions]


@regions_router.post("", response_model=RegionResponse, status_code=201)
def create_region(
    data: RegionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    existing = db.execute(select(Region).where(Region.code == data.code)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail=f"Region with code '{data.code}' already exists.")
    region = Region(**data.model_dump())
    db.add(region)
    db.flush()
    log_action(entity_type="region", entity_id=region.id, action="created",
               actor=current_user, new_val=data.model_dump(), db=db)
    db.commit()
    db.refresh(region)
    return RegionResponse.model_validate(region)


@regions_router.patch("/{region_id}", response_model=RegionResponse)
def update_region(
    region_id: uuid.UUID,
    data: RegionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    region = db.get(Region, region_id)
    if not region:
        raise HTTPException(status_code=404, detail="Region not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(region, field, value)
    log_action(entity_type="region", entity_id=region.id, action="updated",
               actor=current_user, new_val=data.model_dump(exclude_unset=True), db=db)
    db.commit()
    db.refresh(region)
    return RegionResponse.model_validate(region)
