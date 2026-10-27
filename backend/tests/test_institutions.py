"""Tests for institution CRUD endpoints."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.institution import Institution
from app.models.user import User


_INSTITUTION_PAYLOAD = {
    "name": "Alpha Engineering College",
    "permanent_id": "ALPHA-001",
    "state": "Maharashtra",
    "district": "Pune",
    "is_active": True,
}


def test_create_institution_as_admin(
    client: TestClient,
    admin_token: str,
    test_admin: User,
):
    """Admin can create an institution and receives 201."""
    response = client.post(
        "/api/v1/institutions",
        json=_INSTITUTION_PAYLOAD,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Alpha Engineering College"
    assert data["permanent_id"] == "ALPHA-001"
    assert "id" in data


def test_create_institution_duplicate_permanent_id(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_institution: Institution,
):
    """Creating a second institution with an existing permanent_id returns 409."""
    response = client.post(
        "/api/v1/institutions",
        json={"name": "Duplicate College", "permanent_id": "TEST-001", "is_active": True},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 409


def test_get_institution(
    client: TestClient,
    admin_token: str,
    test_institution: Institution,
):
    """GET /institutions/{id} returns 200 with institution data."""
    response = client.get(
        f"/api/v1/institutions/{test_institution.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_institution.id)
    assert data["name"] == "Test Engineering College"
    assert data["permanent_id"] == "TEST-001"


def test_list_institutions_with_search(
    client: TestClient,
    admin_token: str,
    test_db: Session,
    test_admin: User,
):
    """Listing institutions with a name filter returns only matching results."""
    # Create two institutions
    i1 = Institution(name="Alpha College of Engineering", permanent_id="ACE-001", is_active=True)
    i2 = Institution(name="Beta Management Institute", permanent_id="BMI-001", is_active=True)
    test_db.add_all([i1, i2])
    test_db.commit()

    response = client.get(
        "/api/v1/institutions?name=Alpha",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Alpha College of Engineering"


def test_update_institution(
    client: TestClient,
    admin_token: str,
    test_institution: Institution,
):
    """PATCH /institutions/{id} returns 200 with updated data."""
    response = client.patch(
        f"/api/v1/institutions/{test_institution.id}",
        json={"state": "Karnataka", "district": "Bengaluru"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["state"] == "Karnataka"
    assert data["district"] == "Bengaluru"
    # Name should be unchanged
    assert data["name"] == "Test Engineering College"


def test_create_institution_unauthorized(
    client: TestClient,
    test_db: Session,
    test_bureau_rb,
):
    """A regional_officer cannot create institutions (403)."""
    from app.models.user import UserRole
    from app.core.security import create_access_token, hash_password

    officer = User(
        email="regional@aicte.gov.in",
        hashed_password=hash_password("Officer@1234"),
        full_name="Regional Officer",
        role=UserRole.regional_officer,
        is_active=True,
    )
    test_db.add(officer)
    test_db.commit()
    test_db.refresh(officer)

    token = create_access_token(
        user_id=officer.id,
        email=officer.email,
        role=officer.role,
    )

    response = client.post(
        "/api/v1/institutions",
        json={"name": "Unauthorized College", "is_active": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
