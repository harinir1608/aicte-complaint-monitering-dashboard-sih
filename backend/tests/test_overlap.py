"""Tests for overlap detection logic and API endpoints."""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapAlertStatus, MatchType
from app.models.user import User


def _make_case(
    db: Session,
    bureau: Bureau,
    institution: Institution = None,
    subject: str = "Fee dispute",
    case_number: str = "TEST-2024-000001",
    actor_id=None,
) -> Case:
    case = Case(
        case_number=case_number,
        subject=subject,
        status=CaseStatus.received,
        priority=CasePriority.normal,
        bureau_id=bureau.id,
        institution_id=institution.id if institution else None,
        created_by_id=actor_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


def _make_institution(db: Session, name: str, permanent_id: str = None) -> Institution:
    inst = Institution(name=name, permanent_id=permanent_id, is_active=True)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _make_overlap_alert(
    db: Session,
    case1: Case,
    case2: Case,
    institution: Institution = None,
    match_type: MatchType = MatchType.exact_id,
    match_score: float = 100.0,
) -> OverlapAlert:
    import uuid
    from datetime import datetime, timezone
    alert = OverlapAlert(
        alert_number=f"OA-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}",
        case_id_incoming=case1.id,
        case_id_existing=case2.id,
        institution_id=institution.id if institution else None,
        match_type=match_type,
        match_score=match_score,
        status=OverlapAlertStatus.pending_review,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


# ── Institution matching tests ────────────────────────────────────────────────

def test_exact_institution_match(
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
    test_admin: User,
):
    """Two cases with the same institution_id should produce an overlap candidate."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig

    institution = _make_institution(test_db, "Common College", "COMMON-001")
    case1 = _make_case(
        test_db, test_bureau_rb, institution, "Fee dispute case 1", "RB-2024-000001", test_admin.id
    )
    case2 = _make_case(
        test_db, test_bureau_pgrc, institution, "Fee dispute case 2", "PGRC-2024-000001", test_admin.id
    )

    engine = OverlapEngine(test_db, MatchConfig(institution_name_threshold=80.0))
    candidates = engine.find_overlaps_for_case(case1)

    # Should find case2 as a candidate
    candidate_ids = [c.candidate_case.id for c in candidates]
    assert case2.id in candidate_ids


def test_fuzzy_institution_match(
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
    test_admin: User,
):
    """'Progressive College' vs 'Progressive Management College' should match above threshold."""
    from app.matching.institution_matcher import InstitutionMatcher
    from app.matching.normalizer import normalize_institution_name

    inst1 = _make_institution(test_db, "Progressive College", "PROG-001")
    inst2 = _make_institution(test_db, "Progressive Management College", "PROG-002")

    matcher = InstitutionMatcher()
    n1 = normalize_institution_name(inst1.name)
    n2 = normalize_institution_name(inst2.name)
    score = matcher._best_score(n1, n2, [])
    # Fuzzy match should be above 60
    assert score > 60.0, f"Expected score > 60, got {score}"


def test_no_overlap_different_institutions(
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
    test_admin: User,
):
    """Two completely different institution names should not produce high overlap."""
    from app.matching.institution_matcher import InstitutionMatcher
    from app.matching.normalizer import normalize_institution_name

    matcher = InstitutionMatcher()
    n1 = normalize_institution_name("Alpha Engineering Institute of Technology")
    n2 = normalize_institution_name("Gamma Polytechnic School of Arts")
    score = matcher._best_score(n1, n2, [])
    # Should be low similarity
    assert score < 50.0, f"Expected score < 50, got {score}"


def test_overlap_alert_creation(
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
    test_admin: User,
):
    """run_overlap_check on a case with matching institution creates an OverlapAlert."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig
    from sqlalchemy import select

    institution = _make_institution(test_db, "Shared University", "SHARED-001")
    case1 = _make_case(test_db, test_bureau_rb, institution, "Dispute A", "RB-2024-001111")
    case2 = _make_case(test_db, test_bureau_pgrc, institution, "Dispute B", "PGRC-2024-001111")

    engine = OverlapEngine(test_db, MatchConfig())
    created_alerts = engine.run_overlap_check(case1.id, test_db)

    # Check alerts were persisted
    alerts = test_db.execute(select(OverlapAlert)).scalars().all()
    assert len(alerts) >= 1
    # Alert should reference both cases
    alert = alerts[0]
    ids = {alert.case_id_incoming, alert.case_id_existing}
    assert case1.id in ids
    assert case2.id in ids


def test_no_duplicate_active_alerts(
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
    test_admin: User,
):
    """Running overlap check twice on the same pair creates only 1 active alert."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig
    from sqlalchemy import select

    institution = _make_institution(test_db, "Duplicate Check College", "DUP-001")
    case1 = _make_case(test_db, test_bureau_rb, institution, "Dup dispute A", "RB-2024-002222")
    case2 = _make_case(test_db, test_bureau_pgrc, institution, "Dup dispute B", "PGRC-2024-002222")

    engine = OverlapEngine(test_db, MatchConfig())
    engine.run_overlap_check(case1.id, test_db)
    engine.run_overlap_check(case1.id, test_db)

    alerts = test_db.execute(
        select(OverlapAlert).where(OverlapAlert.status == OverlapAlertStatus.pending_review)
    ).scalars().all()

    # Count alerts involving this pair
    pair_alerts = [
        a for a in alerts
        if (a.case_id_incoming == case1.id and a.case_id_existing == case2.id)
        or (a.case_id_incoming == case2.id and a.case_id_existing == case1.id)
    ]
    assert len(pair_alerts) == 1, f"Expected 1 alert, found {len(pair_alerts)}"


def test_false_positive_review(
    client,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
):
    """Reviewing an alert with false_positive updates alert status."""
    institution = _make_institution(test_db, "Review Test College", "RTC-001")
    case1 = _make_case(test_db, test_bureau_rb, institution, "FP Test A", "RB-2024-003333")
    case2 = _make_case(test_db, test_bureau_pgrc, institution, "FP Test B", "PGRC-2024-003333")
    alert = _make_overlap_alert(test_db, case1, case2, institution)

    response = client.post(
        f"/api/v1/overlaps/{alert.id}/review",
        json={"decision": "false_positive", "remarks": "Different issues"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201

    test_db.refresh(alert)
    assert alert.status == OverlapAlertStatus.false_positive


def test_confirmed_related_review(
    client,
    admin_token: str,
    test_admin: User,
    test_db: Session,
    test_bureau_rb: Bureau,
    test_bureau_pgrc: Bureau,
):
    """Reviewing an alert with confirmed_related updates alert status."""
    institution = _make_institution(test_db, "Confirmed College", "CONF-001")
    case1 = _make_case(test_db, test_bureau_rb, institution, "CR Test A", "RB-2024-004444")
    case2 = _make_case(test_db, test_bureau_pgrc, institution, "CR Test B", "PGRC-2024-004444")
    alert = _make_overlap_alert(test_db, case1, case2, institution)

    response = client.post(
        f"/api/v1/overlaps/{alert.id}/review",
        json={"decision": "confirmed_related", "remarks": "Same complaint"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 201

    test_db.refresh(alert)
    assert alert.status == OverlapAlertStatus.confirmed_related
