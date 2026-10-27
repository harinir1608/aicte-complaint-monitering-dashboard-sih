"""Tests for case management endpoints."""
from __future__ import annotations

import re
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.institution import Institution
from app.models.user import User


def _case_payload(bureau_id=None, institution_id=None):
    return {
        "subject": "Fee dispute at institution",
        "priority": "normal",
        "bureau_id": str(bureau_id) if bureau_id else None,
        "institution_id": str(institution_id) if institution_id else None,
    }


def test_create_case(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
):
    """POST /cases returns 201 with auto-generated case_number."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    response = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "case_number" in data
    assert data["case_number"]
    assert data["status"] == "received"


def test_create_case_number_format(
    client: TestClient,
    admin_token: str,
    test_bureau_rb: Bureau,
):
    """Auto-generated case_number matches pattern BUREAUCODE-YYYY-NNNNNN."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    response = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201
    case_number = response.json()["case_number"]
    pattern = r"^[A-Z]+-\d{4}-\d{6}$"
    assert re.match(pattern, case_number), (
        f"case_number '{case_number}' does not match expected pattern"
    )


def test_assign_case(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_rb_officer: User,
    test_bureau_rb: Bureau,
    test_db: Session,
):
    """Assigning a case creates a CaseAssignment record."""
    # Create case
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    # Assign to rb_officer
    assign_resp = client.post(
        f"/api/v1/cases/{case_id}/assign",
        json={"officer_id": str(test_rb_officer.id), "notes": "Initial assignment"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assign_resp.status_code == 201
    assignment_data = assign_resp.json()
    assert assignment_data["assigned_to_id"] == str(test_rb_officer.id)
    assert assignment_data["is_current"] is True

    # Verify in db
    from app.models.case import CaseAssignment
    from sqlalchemy import select
    assignments = test_db.execute(
        select(CaseAssignment).where(CaseAssignment.case_id.in_(
            [a for a in [case_id]]
        ))
    ).scalars().all()
    assert len(assignments) >= 1


def test_transfer_case(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
):
    """Transferring a case to another bureau returns 200 and updates bureau_id."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    transfer_resp = client.post(
        f"/api/v1/cases/{case_id}/transfer",
        json={"target_bureau_id": str(test_bureau_pgrc.id), "reason": "Jurisdiction change"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert transfer_resp.status_code == 200
    data = transfer_resp.json()
    assert data["bureau_id"] == str(test_bureau_pgrc.id)
    assert data["status"] == "transferred"


def test_valid_status_transition(
    client: TestClient,
    admin_token: str,
    test_bureau_rb: Bureau,
):
    """received -> pending_assignment is a valid transition."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    status_resp = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "pending_assignment"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "pending_assignment"


def test_invalid_status_transition(
    client: TestClient,
    admin_token: str,
    test_bureau_rb: Bureau,
):
    """received -> disposed directly is an invalid transition (422)."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    status_resp = client.patch(
        f"/api/v1/cases/{case_id}/status",
        json={"new_status": "disposed"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert status_resp.status_code == 422


def test_get_case_history(
    client: TestClient,
    admin_token: str,
    test_bureau_rb: Bureau,
):
    """GET /cases/{id}/history returns a list of CaseAction records."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)
    create_resp = client.post(
        "/api/v1/cases",
        json=payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert create_resp.status_code == 201
    case_id = create_resp.json()["id"]

    history_resp = client.get(
        f"/api/v1/cases/{case_id}/history",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert isinstance(history, list)
    # At minimum, one action from case creation
    assert len(history) >= 1
    assert history[0]["case_id"] == case_id


def test_link_related_cases(
    client: TestClient,
    admin_token: str,
    test_bureau_rb: Bureau,
):
    """POST /cases/{id}/related-cases creates a RelatedCase link."""
    payload = _case_payload(bureau_id=test_bureau_rb.id)

    # Create two cases
    resp1 = client.post("/api/v1/cases", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    resp2 = client.post("/api/v1/cases", json={**payload, "subject": "Related issue"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert resp1.status_code == 201
    assert resp2.status_code == 201

    case1_id = resp1.json()["id"]
    case2_id = resp2.json()["id"]

    link_resp = client.post(
        f"/api/v1/cases/{case1_id}/related-cases",
        json={"related_case_id": case2_id, "relationship_type": "similar_issue", "rationale": "Same institution"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert link_resp.status_code == 201
    data = link_resp.json()
    # Should contain both case IDs
    assert str(case1_id) in [data["case_id_1"], data["case_id_2"]]
    assert str(case2_id) in [data["case_id_1"], data["case_id_2"]]


def test_case_access_control(
    client: TestClient,
    test_db: Session,
    admin_token: str,
    test_admin: User,
    test_rb_officer: User,
    rb_officer_token: str,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
):
    """An RB officer cannot see cases that belong only to the PGRC bureau through list filtering."""
    # Create a PGRC-only case directly in DB
    pgrc_case = Case(
        case_number="PGRC-2024-999999",
        subject="PGRC Only Case",
        status=CaseStatus.received,
        priority=CasePriority.normal,
        bureau_id=test_bureau_pgrc.id,
        created_by_id=test_admin.id,
    )
    test_db.add(pgrc_case)
    test_db.commit()
    test_db.refresh(pgrc_case)

    # Admin can see it
    admin_resp = client.get(
        f"/api/v1/cases/{pgrc_case.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert admin_resp.status_code == 200

    # RB officer can access the case detail (no detail-level restriction in current impl),
    # but their list view filters by bureau
    rb_list_resp = client.get(
        "/api/v1/cases",
        headers={"Authorization": f"Bearer {rb_officer_token}"},
    )
    assert rb_list_resp.status_code == 200
    # RB officer's list should not contain PGRC-only cases
    rb_case_ids = [c["id"] for c in rb_list_resp.json()["items"]]
    assert str(pgrc_case.id) not in rb_case_ids
