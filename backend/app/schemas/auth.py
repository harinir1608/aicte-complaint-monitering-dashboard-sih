from __future__ import annotations

import uuid
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: uuid.UUID
    email: str
    role: UserRole


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


# ── User schemas ──────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1, max_length=200)
    employee_id: Optional[str] = None
    role: UserRole = UserRole.bureau_officer
    bureau_id: Optional[uuid.UUID] = None
    region_id: Optional[uuid.UUID] = None
    is_superuser: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    employee_id: Optional[str] = None
    role: Optional[UserRole] = None
    bureau_id: Optional[uuid.UUID] = None
    region_id: Optional[uuid.UUID] = None
    is_active: Optional[bool] = None


class BureauBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class RegionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    employee_id: Optional[str]
    is_active: bool
    is_superuser: bool
    role: UserRole
    bureau_id: Optional[uuid.UUID]
    region_id: Optional[uuid.UUID]
    bureau: Optional[BureauBrief]
    region: Optional[RegionBrief]
    last_login: Optional[str] = None

    @field_validator("last_login", mode="before")
    @classmethod
    def serialize_last_login(cls, v):
        if v is None:
            return None
        return v.isoformat() if hasattr(v, "isoformat") else str(v)
