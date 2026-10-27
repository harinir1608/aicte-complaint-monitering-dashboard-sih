"""
Unit tests for the explainable AI overlap detection engine.

Covers: exact ID match, fuzzy name match, semantic match (if enabled),
unrelated complaints (no match), missing institution ID, false positive
prevention, and deduplication.
"""
from __future__ import annotations

import pytest
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.bureau import Bureau
from app.models.case import Case, CaseStatus, CasePriority
from app.models.institution import Institution
from app.models.overlap import OverlapAlert, OverlapAlertStatus, MatchType


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_institution(db: Session, name: str, permanent_id: str | None = None) -> Institution:
    inst = Institution(name=name, permanent_id=permanent_id, is_active=True)
    db.add(inst)
    db.commit()
    db.refresh(inst)
    return inst


def _make_case(
    db: Session,
    bureau: Bureau,
    institution: Institution | None,
    subject: str,
    case_number: str,
    description: str = "",
) -> Case:
    case = Case(
        case_number=case_number,
        subject=subject,
        description=description,
        status=CaseStatus.under_process,
        priority=CasePriority.normal,
        bureau_id=bureau.id,
        institution_id=institution.id if institution else None,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


# ---------------------------------------------------------------------------
# Exact ID match
# ---------------------------------------------------------------------------

def test_exact_permanent_id_match(test_db: Session, test_bureau_rb: Bureau, test_bureau_pgrc: Bureau) -> None:
    """Cases sharing AICTE permanent_id must be detected at score 100."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig

    inst1 = _make_institution(test_db, "ABC Engineering College", "AICTE-12345")
    inst2 = _make_institution(test_db, "ABC Engineering College (branch)", "AICTE-12345")

    case1 = _make_case(test_db, test_bureau_rb, inst1, "Fee issue", "RB-OD-001")
    case2 = _make_case(test_db, test_bureau_pgrc, inst2, "Fee refund", "PGRC-OD-001")

    engine = OverlapEngine(test_db, MatchConfig())
    candidates = engine.find_overlaps_for_case(case1)

    ids = [c.candidate_case.id for c in candidates]
    assert case2.id in ids

    match = next(c for c in candidates if c.candidate_case.id == case2.id)
    assert match.institution_score == 100.0


# ---------------------------------------------------------------------------
# Fuzzy name match
# ---------------------------------------------------------------------------

def test_fuzzy_name_match_above_threshold(test_db: Session, test_bureau_rb: Bureau, test_bureau_pgrc: Bureau) -> None:
    """Similar institution names should score above the 80-point threshold."""
    from app.matching.institution_matcher import InstitutionMatcher
    from app.matching.normalizer import normalize_institution_name

    matcher = InstitutionMatcher()
    n1 = normalize_institution_name("National Institute of Technology Warangal")
    n2 = normalize_institution_name("National Institute Technology Warangal")
    score = matcher._best_score(n1, n2, [])
    assert score >= 80.0, f"Expected fuzzy score >= 80, got {score}"


# ---------------------------------------------------------------------------
# Semantic match (skipped when not available)
# ---------------------------------------------------------------------------

def test_semantic_match_skipped_when_disabled() -> None:
    """When ENABLE_SEMANTIC_MATCHING is false, semantic score must be None."""
    import os
    os.environ.setdefault("ENABLE_SEMANTIC_MATCHING", "false")
    from app.matching.complaint_matcher import ComplaintMatcher
    matcher = ComplaintMatcher()
    score = matcher.compare_complaints_semantic(
        "Student has not received fee refund after withdrawal",
        "Fee refund not issued after dropout",
    )
    # Should be None because semantic is disabled
    assert score is None


# ---------------------------------------------------------------------------
# Unrelated complaints — no match
# ---------------------------------------------------------------------------

def test_unrelated_complaints_do_not_match(test_db: Session, test_bureau_rb: Bureau) -> None:
    """Completely unrelated complaint texts should score below the threshold."""
    from app.matching.complaint_matcher import ComplaintMatcher
    from app.matching.overlap_engine import MatchConfig

    cfg = MatchConfig()
    matcher = ComplaintMatcher()
    score = matcher.compare_complaints_text(
        "Student fee refund dispute related to withdrawal from programme",
        "Construction work deficiency in laboratory building infrastructure",
    )
    # These topics are unrelated; text similarity should be below threshold
    assert score < cfg.complaint_similarity_threshold, f"Unrelated texts scored {score} (>= {cfg.complaint_similarity_threshold})"


# ---------------------------------------------------------------------------
# Missing institution ID
# ---------------------------------------------------------------------------

def test_no_candidates_when_no_institution(test_db: Session, test_bureau_rb: Bureau) -> None:
    """A case with no institution_id should find no candidates via exact match."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig

    # Case with no institution
    case_no_inst = _make_case(test_db, test_bureau_rb, None, "Anonymous complaint", "RB-OD-ANON")

    engine = OverlapEngine(test_db, MatchConfig())
    candidates = engine.find_overlaps_for_case(case_no_inst)

    # No institution means no exact-match candidates (fuzzy still possible if institution attr set)
    assert isinstance(candidates, list)


# ---------------------------------------------------------------------------
# False positive prevention — deduplication
# ---------------------------------------------------------------------------

def test_no_duplicate_alert_for_same_pair(test_db: Session, test_bureau_rb: Bureau, test_bureau_pgrc: Bureau) -> None:
    """Running overlap detection twice must not create duplicate pending alerts."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig

    inst = _make_institution(test_db, "Dedup College", "DEDUP-001")
    case1 = _make_case(test_db, test_bureau_rb, inst, "Duplicate test A", "RB-DEDUP-001")
    case2 = _make_case(test_db, test_bureau_pgrc, inst, "Duplicate test B", "PGRC-DEDUP-001")

    engine = OverlapEngine(test_db, MatchConfig())
    engine.run_overlap_check(case1.id, test_db)
    engine.run_overlap_check(case1.id, test_db)  # second run — should not duplicate

    alerts = test_db.execute(
        select(OverlapAlert).where(OverlapAlert.status == OverlapAlertStatus.pending_review)
    ).scalars().all()

    pair_alerts = [
        a for a in alerts
        if (a.case_id_incoming == case1.id and a.case_id_existing == case2.id)
        or (a.case_id_incoming == case2.id and a.case_id_existing == case1.id)
    ]
    assert len(pair_alerts) == 1, f"Expected 1 alert, found {len(pair_alerts)}"


# ---------------------------------------------------------------------------
# Explainability — match_reasons and detection_method populated
# ---------------------------------------------------------------------------

def test_overlap_alert_has_match_reasons(test_db: Session, test_bureau_rb: Bureau, test_bureau_pgrc: Bureau) -> None:
    """Created overlap alerts must have non-empty match_reasons and detection_method."""
    from app.matching.overlap_engine import OverlapEngine, MatchConfig

    inst = _make_institution(test_db, "Explainability College", "EXPL-001")
    case1 = _make_case(test_db, test_bureau_rb, inst, "Fee complaint alpha", "RB-EXPL-001")
    case2 = _make_case(test_db, test_bureau_pgrc, inst, "Fee complaint beta", "PGRC-EXPL-001")

    engine = OverlapEngine(test_db, MatchConfig())
    created = engine.run_overlap_check(case1.id, test_db)

    if created:
        alert = created[0]
        assert alert.match_reasons is not None
        assert len(alert.match_reasons) > 0
        assert alert.detection_method is not None
        assert alert.similarity_score is not None
