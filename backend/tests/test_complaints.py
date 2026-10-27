"""Tests for complaint CRUD endpoints."""
from __future__ import annotations

import re
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.institution import Institution
from app.models.user import User


def _complaint_payload(bureau_id=None, institution_id=None):
    return {
        "subject": "Excessive fee charged by institution",
        "source": "portal",
        "received_date": str(date.today()),
        "bureau_id": str(bureau_id) if bureau_id else None,
        "institution_id": str(institution_id) if institution_id else None,
        "priority": "normal",
    }


def test_create_complaint(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
):
    """POST /complaints returns 201 with auto-generated complaint_number."""
    payload = _complaint_payload(bureau_id=test_bureau_rb.id)
    response = client.post(
        "/api/v1/complaints",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "complaint_number" in data
    assert data["complaint_number"]
    assert data["subject"] == "Excessive fee charged by institution"


def test_create_complaint_number_format(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
):
    """Auto-generated complaint_number matches pattern BUREAUCODE-YYYY-NNNNNN."""
    payload = _complaint_payload(bureau_id=test_bureau_rb.id)
    response = client.post(
        "/api/v1/complaints",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    complaint_number = response.json()["complaint_number"]
    # Pattern: e.g. RB-2024-000001
    pattern = r"^[A-Z]+-\d{4}-\d{6}$"
    assert re.match(pattern, complaint_number), (
        f"complaint_number '{complaint_number}' does not match expected pattern"
    )


def test_get_complaint(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
):
    """GET /complaints/{id} returns 200 with complaint data."""
    # Create
    payload = _complaint_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/complaints",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    complaint_id = create_resp.json()["id"]

    # Retrieve
    get_resp = client.get(
        f"/api/v1/complaints/{complaint_id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == complaint_id
    assert data["subject"] == "Excessive fee charged by institution"


def test_list_complaints_filtered_by_bureau(
    client: TestClient,
    test_db: Session,
    test_admin: User,
    admin_token: str,
    test_rb_officer: User,
    rb_officer_token: str,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
):
    """An RB officer only sees complaints belonging to their bureau."""
    from app.models.complaint import Complaint, ComplaintSource, ComplaintStatus, ComplaintPriority

    # Create RB complaint
    rb_complaint = Complaint(
        complaint_number="RB-2024-000001",
        subject="RB Complaint",
        source=ComplaintSource.portal,
        received_date=date.today(),
        bureau_id=test_bureau_rb.id,
        status=ComplaintStatus.received,
        priority=ComplaintPriority.normal,
        created_by_id=test_admin.id,
    )
    # Create PGRC complaint
    pgrc_complaint = Complaint(
        complaint_number="PGRC-2024-000001",
        subject="PGRC Complaint",
        source=ComplaintSource.portal,
        received_date=date.today(),
        bureau_id=test_bureau_pgrc.id,
        status=ComplaintStatus.received,
        priority=ComplaintPriority.normal,
        created_by_id=test_admin.id,
    )
    test_db.add_all([rb_complaint, pgrc_complaint])
    test_db.commit()

    # Admin sees all
    admin_resp = client.get(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.json()["total"] == 2

    # RB officer sees only RB complaints
    rb_resp = client.get(
        "/api/v1/complaints",
        headers={"Authorization": f"Bearer {rb_officer_token}"},
    )
    assert rb_resp.status_code == 200
    rb_data = rb_resp.json()
    assert rb_data["total"] == 1
    assert rb_data["items"][0]["subject"] == "RB Complaint"


def test_update_complaint_status(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
):
    """PATCH /complaints/{id} updates complaint fields."""
    payload = _complaint_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/complaints",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    complaint_id = create_resp.json()["id"]

    # Update priority and status
    update_resp = client.patch(
        f"/api/v1/complaints/{complaint_id}",
        json={"priority": "high", "status": "pending_assignment"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["priority"] == "high"
    assert updated["status"] == "pending_assignment"
