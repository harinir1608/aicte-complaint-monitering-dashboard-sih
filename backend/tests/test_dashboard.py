"""Tests for dashboard summary, trends, and overdue endpoints."""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.complaint import Complaint, ComplaintSource, ComplaintStatus, ComplaintPriority
from app.models.institution import Institution
from app.models.user import User


def _add_case(
    db: Session,
    bureau: Bureau,
    status: CaseStatus = CaseStatus.received,
    expected_disposal_date: date = None,
    case_num: str = None,
    actor_id=None,
) -> Case:
    import uuid
    num = case_num or f"RB-2024-{str(uuid.uuid4())[:6].upper()}"
    case = Case(
        case_number=num,
        subject="Test case",
        status=status,
        priority=CasePriority.normal,
        bureau_id=bureau.id,
        expected_disposal_date=expected_disposal_date,
        created_by_id=actor_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def _add_complaint(
    db: Session,
    bureau: Bureau,
    actor_id=None,
    comp_num: str = None,
) -> Complaint:
    import uuid
    num = comp_num or f"RB-2024-{str(uuid.uuid4())[:6].upper()}"
    c = Complaint(
        complaint_number=num,
        subject="Test complaint",
        source=ComplaintSource.portal,
        received_date=date.today(),
        bureau_id=bureau.id,
        status=ComplaintStatus.received,
        priority=ComplaintPriority.normal,
        created_by_id=actor_id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def test_dashboard_summary_counts(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Summary counts reflect the actual data in the database."""
    # Create 2 complaints
    _add_complaint(test_db, test_bureau_rb, test_admin.id, "RB-2024-C00001")
    _add_complaint(test_db, test_bureau_rb, test_admin.id, "RB-2024-C00002")

    # Create 3 cases (2 received, 1 disposed)
    _add_case(test_db, test_bureau_rb, CaseStatus.received, case_num="RB-2024-000101", actor_id=test_admin.id)
    _add_case(test_db, test_bureau_rb, CaseStatus.received, case_num="RB-2024-000102", actor_id=test_admin.id)
    _add_case(test_db, test_bureau_rb, CaseStatus.disposed, case_num="RB-2024-000103", actor_id=test_admin.id)

    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()

    assert data["total_complaints"] == 2
    assert data["total_cases"] == 3
    assert data["active_cases"] == 2  # 2 received are active
    assert data["disposed"] == 1


def test_dashboard_trends(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Trends endpoint returns a list (may be empty if no data in last 12 months)."""
    # Create some data
    _add_complaint(test_db, test_bureau_rb, test_admin.id, "RB-2024-T00001")

    response = client.get(
        "/api/v1/dashboard/trends?months=12",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Each trend point should have the required fields
    if data:
        trend = data[0]
        assert "period" in trend
        assert "intake" in trend
        assert "disposed" in trend


def test_overdue_count(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Cases with past expected_disposal_date are counted as overdue."""
    past_date = date.today() - timedelta(days=10)
    future_date = date.today() + timedelta(days=10)

    # 1 overdue case
    _add_case(
        test_db, test_bureau_rb,
        status=CaseStatus.under_process,
        expected_disposal_date=past_date,
        case_num="RB-2024-OD0001",
        actor_id=test_admin.id,
    )
    # 1 not overdue case
    _add_case(
        test_db, test_bureau_rb,
        status=CaseStatus.under_process,
        expected_disposal_date=future_date,
        case_num="RB-2024-OD0002",
        actor_id=test_admin.id,
    )
    # 1 disposed (should not be counted as overdue even if past date)
    _add_case(
        test_db, test_bureau_rb,
        status=CaseStatus.disposed,
        expected_disposal_date=past_date,
        case_num="RB-2024-OD0003",
        actor_id=test_admin.id,
    )

    response = client.get(
        "/api/v1/dashboard/summary",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["overdue_cases"] == 1, (
        f"Expected 1 overdue case, got {data['overdue_cases']}"
    )
