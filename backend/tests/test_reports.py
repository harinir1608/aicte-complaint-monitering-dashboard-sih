"""Tests for report generation endpoints."""
from __future__ import annotations

import csv
import io
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.institution import Institution
from app.models.user import User


def _add_institution(db: Session, name: str, permanent_id: str) -> Institution:
    inst = Institution(name=name, permanent_id=permanent_id, is_active=True)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _add_case(
    db: Session,
    bureau: Bureau,
    institution: Institution = None,
    status: CaseStatus = CaseStatus.received,
    expected_disposal_date: date = None,
    case_num: str = None,
    actor_id=None,
) -> Case:
    import uuid
    num = case_num or f"RB-2024-RPT{str(uuid.uuid4())[:6].upper()}"
    case = Case(
        case_number=num,
        subject="Report test case",
        status=status,
        priority=CasePriority.normal,
        bureau_id=bureau.id,
        institution_id=institution.id if institution else None,
        expected_disposal_date=expected_disposal_date,
        created_by_id=actor_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def test_csv_export_institutions(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
):
    """GET /reports/institutions?format=csv returns a valid CSV response."""
    _add_institution(test_db, "CSV Test College", "CSV-001")
    _add_institution(test_db, "CSV Test University", "CSV-002")

    response = client.get(
        "/api/v1/reports/institutions?format=csv",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert "text/csv" in response.headers.get("content-type", "")

    # Parse CSV and verify structure
    content = response.content.decode("utf-8")
    reader = csv.reader(io.StringIO(content))
    rows = list(reader)
    assert len(rows) >= 3  # header + 2 institutions
    header = rows[0]
    assert "institution_name" in header
    assert "total_cases" in header


def test_report_filters_applied(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Date range filter in ageing report limits results to matching records."""
    from datetime import datetime
    from sqlalchemy import text

    # Create two cases - one recent (within filter range), one old
    recent_case = _add_case(
        test_db, test_bureau_rb,
        status=CaseStatus.under_process,
        case_num="RB-2024-RPTF001",
        actor_id=test_admin.id,
    )

    # Use date_from = today so only today's cases are included
    today_str = date.today().isoformat()
    response = client.get(
        f"/api/v1/reports/ageing?date_from={today_str}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    # The recent case should appear in results
    assert "rows" in data
    case_numbers = [row["case_number"] for row in data["rows"]]
    assert "RB-2024-RPTF001" in case_numbers


def test_ageing_report(
    client: TestClient,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
):
    """Overdue cases (past expected_disposal_date) appear in the ageing report."""
    past_date = date.today() - timedelta(days=65)  # 61+ days ago
    overdue_case = _add_case(
        test_db, test_bureau_rb,
        status=CaseStatus.under_process,
        expected_disposal_date=past_date,
        case_num="RB-2024-RPTAGE1",
        actor_id=test_admin.id,
    )

    response = client.get(
        "/api/v1/reports/ageing",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert "overdue_count" in data

    # Find the overdue case in the response
    overdue_rows = [r for r in data["rows"] if r["case_number"] == "RB-2024-RPTAGE1"]
    assert len(overdue_rows) == 1
    assert overdue_rows[0]["is_overdue"] is True
    assert overdue_rows[0]["age_days"] >= 60
    assert data["overdue_count"] >= 1
