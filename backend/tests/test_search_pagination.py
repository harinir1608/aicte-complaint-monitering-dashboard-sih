"""Tests for search and pagination behavior."""
from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.institution import Institution
from app.models.user import User


def _create_institutions(db: Session, count: int = 25) -> list[Institution]:
    institutions = []
    for i in range(count):
        inst = Institution(
            name=f"Test Institution Number {i:03d}",
            permanent_id=f"INST-{i:04d}",
            state="Maharashtra" if i % 2 == 0 else "Karnataka",
            is_active=True,
        )
        db.add(inst)
        institutions.append(inst)
    db.commit()
    for inst in institutions:
        db.refresh(inst)
    return institutions


def _create_cases(db: Session, bureau: Bureau, count: int = 25, actor_id=None) -> list[Case]:
    import uuid as _uuid
    cases = []
    for i in range(count):
        status = CaseStatus.received if i % 3 != 0 else CaseStatus.disposed
        priority = CasePriority.high if i % 5 == 0 else CasePriority.normal
        case = Case(
            case_number=f"RB-2024-{i:06d}",
            subject=f"Test Case Subject {i:03d}",
            status=status,
            priority=priority,
            bureau_id=bureau.id,
            created_by_id=actor_id,
        )
        db.add(case)
        cases.append(case)
    db.commit()
    for case in cases:
        db.refresh(case)
    return cases


def test_institution_search_by_name(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
):
    """Search institutions by name filters to matching results only."""
    _create_institutions(test_db, count=5)

    response = client.get(
        "/api/v1/institutions?name=Number+001",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Number 001" in data["items"][0]["name"]


def test_institution_search_by_permanent_id(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
):
    """Search institutions by permanent_id filters correctly."""
    _create_institutions(test_db, count=5)

    response = client.get(
        "/api/v1/institutions?permanent_id=INST-0003",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["permanent_id"] == "INST-0003"


def test_case_list_pagination(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Second page of case listing returns the correct offset items."""
    _create_cases(test_db, test_bureau_rb, count=25, actor_id=test_admin.id)

    # Page 1 - 20 items
    resp_p1 = client.get(
        "/api/v1/cases?page=1&page_size=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_p1.status_code == 200
    p1_data = resp_p1.json()
    assert len(p1_data["items"]) == 10
    assert p1_data["total"] == 25
    assert p1_data["pages"] == 3

    # Page 2
    resp_p2 = client.get(
        "/api/v1/cases?page=2&page_size=10",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_p2.status_code == 200
    p2_data = resp_p2.json()
    assert len(p2_data["items"]) == 10

    # Pages 1 and 2 should not have the same items
    p1_ids = {item["id"] for item in p1_data["items"]}
    p2_ids = {item["id"] for item in p2_data["items"]}
    assert p1_ids.isdisjoint(p2_ids), "Page 1 and Page 2 should not share items"


def test_case_list_filter_by_status(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Filtering cases by status returns only matching cases."""
    _create_cases(test_db, test_bureau_rb, count=10, actor_id=test_admin.id)

    response = client.get(
        "/api/v1/cases?status=disposed&page_size=50",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # All returned cases must have status 'disposed'
    for item in data["items"]:
        assert item["status"] == "disposed", (
            f"Expected status 'disposed', got '{item['status']}'"
        )


def test_case_list_filter_by_priority(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Filtering cases by priority returns only matching cases."""
    _create_cases(test_db, test_bureau_rb, count=10, actor_id=test_admin.id)

    response = client.get(
        "/api/v1/cases?priority=high&page_size=50",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["priority"] == "high", (
            f"Expected priority 'high', got '{item['priority']}'"
        )
