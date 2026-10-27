"""
Cross-bureau conflict detection service.

Detects potentially conflicting or parallel actions across bureaus using
configurable rule-based detection. Each rule produces explicit evidence and
a human-readable description. Conflict detection is separate from overlap
detection: overlaps find similar cases; conflicts find coordination problems.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.case import Case, CaseAction, CaseActionType, CaseStatus
from app.models.conflict import ConflictAlert, ConflictSeverity, ConflictStatus
from app.models.institution import Institution

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rule configuration — tweak thresholds here, not in the rule bodies
# ---------------------------------------------------------------------------

CONFLICT_RULES_CONFIG: dict[str, Any] = {
    "multi_bureau_same_issue": {
        "enabled": True,
        "severity": ConflictSeverity.high,
        "description": (
            "Multiple bureaus have active cases for the same institution. "
            "Coordination is recommended to avoid duplicated effort or conflicting decisions."
        ),
        "recommended_action": (
            "Designate a lead bureau and schedule a cross-bureau coordination meeting."
        ),
    },
    "overlapping_officer_actions": {
        "enabled": True,
        "severity": ConflictSeverity.medium,
        "description": (
            "Different officers across bureaus are performing actions on related cases "
            "for the same institution at the same time. Decisions may conflict."
        ),
        "recommended_action": (
            "Notify both officers and request a joint review before finalising actions."
        ),
    },
    "competing_deadlines": {
        "enabled": True,
        "severity": ConflictSeverity.medium,
        "deadline_proximity_days": 7,
        "description": (
            "Multiple active cases for this institution have expected disposal dates "
            "within 7 days of each other. Simultaneous closures may overburden officers "
            "or produce inconsistent outcomes."
        ),
        "recommended_action": (
            "Stagger deadlines or assign a dedicated coordination officer."
        ),
    },
    "transfer_while_related_active": {
        "enabled": True,
        "severity": ConflictSeverity.high,
        "description": (
            "A case for this institution has been transferred or escalated while another "
            "related case remains active in a different bureau. The receiving bureau may "
            "be unaware of the parallel case."
        ),
        "recommended_action": (
            "Inform the receiving bureau of the parallel active case and coordinate."
        ),
    },
}

_ACTIVE_STATUSES = [
    CaseStatus.received,
    CaseStatus.pending_assignment,
    CaseStatus.under_process,
    CaseStatus.awaiting_information,
    CaseStatus.transferred,
    CaseStatus.escalated,
]


# ---------------------------------------------------------------------------
# Individual rule functions
# ---------------------------------------------------------------------------

def _rule_multi_bureau(cases: list[Case]) -> Optional[dict]:
    cfg = CONFLICT_RULES_CONFIG["multi_bureau_same_issue"]
    if not cfg["enabled"]:
        return None

    active = [c for c in cases if c.status in _ACTIVE_STATUSES]
    bureau_ids = list({str(c.bureau_id) for c in active if c.bureau_id})

    if len(bureau_ids) < 2:
        return None

    return {
        "rule": "multi_bureau_same_issue",
        "case_ids": [str(c.id) for c in active],
        "bureau_ids": bureau_ids,
        "severity": cfg["severity"],
        "rule_description": cfg["description"],
        "recommended_action": cfg["recommended_action"],
        "evidence": {
            "active_case_numbers": [c.case_number for c in active],
            "bureau_count": len(bureau_ids),
        },
    }


def _rule_overlapping_actions(cases: list[Case], db: Session) -> Optional[dict]:
    cfg = CONFLICT_RULES_CONFIG["overlapping_officer_actions"]
    if not cfg["enabled"]:
        return None

    active = [c for c in cases if c.status in _ACTIVE_STATUSES and c.bureau_id]
    if len(active) < 2:
        return None

    # Find cases with recent actions (last 3 days) across different bureaus
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    bureau_recent: dict[str, list[str]] = {}
    for case in active:
        recent_actions = db.execute(
            select(CaseAction).where(
                CaseAction.case_id == case.id,
                CaseAction.performed_at >= cutoff,
            )
        ).scalars().all()
        if recent_actions:
            bk = str(case.bureau_id)
            bureau_recent.setdefault(bk, []).append(case.case_number)

    if len(bureau_recent) < 2:
        return None

    return {
        "rule": "overlapping_officer_actions",
        "case_ids": [str(c.id) for c in active],
        "bureau_ids": list(bureau_recent.keys()),
        "severity": cfg["severity"],
        "rule_description": cfg["description"],
        "recommended_action": cfg["recommended_action"],
        "evidence": {
            "bureaus_with_recent_actions": bureau_recent,
            "action_window_days": 3,
        },
    }


def _rule_competing_deadlines(cases: list[Case]) -> Optional[dict]:
    cfg = CONFLICT_RULES_CONFIG["competing_deadlines"]
    if not cfg["enabled"]:
        return None

    proximity = cfg["deadline_proximity_days"]
    deadline_cases = [
        c for c in cases
        if c.status in _ACTIVE_STATUSES and c.expected_disposal_date is not None
    ]

    if len(deadline_cases) < 2:
        return None

    deadline_cases.sort(key=lambda c: c.expected_disposal_date)  # type: ignore[arg-type, return-value]
    conflicts = []
    for i, c1 in enumerate(deadline_cases):
        for c2 in deadline_cases[i + 1 :]:
            delta = abs((c2.expected_disposal_date - c1.expected_disposal_date).days)  # type: ignore[operator]
            if delta <= proximity:
                conflicts.append((c1, c2, delta))

    if not conflicts:
        return None

    return {
        "rule": "competing_deadlines",
        "case_ids": list({str(c.id) for pair in conflicts for c in (pair[0], pair[1])}),
        "bureau_ids": list({str(c.bureau_id) for pair in conflicts for c in (pair[0], pair[1]) if c.bureau_id}),
        "severity": cfg["severity"],
        "rule_description": cfg["description"],
        "recommended_action": cfg["recommended_action"],
        "evidence": {
            "conflicting_pairs": [
                {
                    "case1": c1.case_number,
                    "case2": c2.case_number,
                    "days_apart": delta,
                }
                for c1, c2, delta in conflicts
            ],
            "proximity_threshold_days": proximity,
        },
    }


def _rule_transfer_while_related(cases: list[Case]) -> Optional[dict]:
    cfg = CONFLICT_RULES_CONFIG["transfer_while_related_active"]
    if not cfg["enabled"]:
        return None

    transferred = [c for c in cases if c.status in (CaseStatus.transferred, CaseStatus.escalated)]
    active_others = [
        c for c in cases
        if c.status in _ACTIVE_STATUSES and c.status not in (CaseStatus.transferred, CaseStatus.escalated)
    ]

    if not transferred or not active_others:
        return None

    # Check that they're in different bureaus
    transferred_bureaus = {str(c.bureau_id) for c in transferred if c.bureau_id}
    active_bureaus = {str(c.bureau_id) for c in active_others if c.bureau_id}
    cross_bureau = transferred_bureaus & active_bureaus
    if not cross_bureau and transferred_bureaus and active_bureaus:
        # Different bureaus — this is the coordination risk
        pass
    elif transferred_bureaus == active_bureaus:
        return None

    return {
        "rule": "transfer_while_related_active",
        "case_ids": [str(c.id) for c in transferred + active_others],
        "bureau_ids": list(transferred_bureaus | active_bureaus),
        "severity": cfg["severity"],
        "rule_description": cfg["description"],
        "recommended_action": cfg["recommended_action"],
        "evidence": {
            "transferred_cases": [c.case_number for c in transferred],
            "still_active_cases": [c.case_number for c in active_others],
            "transferred_bureaus": list(transferred_bureaus),
            "active_other_bureaus": list(active_bureaus),
        },
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_conflict_detection(institution_id, db: Session) -> list[ConflictAlert]:
    """Run all enabled rules for a single institution. Returns newly created alerts."""
    cases = db.execute(
        select(Case).where(Case.institution_id == institution_id)
    ).scalars().all()

    if not cases:
        return []

    triggered = []
    for rule_fn in [
        lambda: _rule_multi_bureau(cases),
        lambda: _rule_overlapping_actions(cases, db),
        lambda: _rule_competing_deadlines(cases),
        lambda: _rule_transfer_while_related(cases),
    ]:
        try:
            result = rule_fn()
            if result:
                triggered.append(result)
        except Exception as exc:
            logger.warning("Conflict rule failed: %s", exc, exc_info=True)

    created = []
    for t in triggered:
        # Dedup: skip if open/acknowledged alert for same institution+rule already exists
        existing = db.execute(
            select(ConflictAlert).where(
                ConflictAlert.institution_id == institution_id,
                ConflictAlert.rule_triggered == t["rule"],
                ConflictAlert.status.in_([ConflictStatus.open, ConflictStatus.acknowledged]),
            )
        ).scalar_one_or_none()
        if existing:
            continue

        alert = ConflictAlert(
            institution_id=institution_id,
            case_ids=t["case_ids"],
            bureau_ids=t["bureau_ids"],
            rule_triggered=t["rule"],
            rule_description=t.get("rule_description"),
            evidence=t.get("evidence"),
            severity=t["severity"],
            recommended_action=t.get("recommended_action"),
            status=ConflictStatus.open,
        )
        db.add(alert)
        created.append(alert)

    if created:
        db.flush()

    return created


def run_global_conflict_scan(db: Session) -> int:
    """Scan all institutions with active cases. Returns total new alerts created."""
    institution_ids = db.execute(
        select(Case.institution_id)
        .where(Case.institution_id.isnot(None), Case.status.in_(_ACTIVE_STATUSES))
        .distinct()
    ).scalars().all()

    total = 0
    for inst_id in institution_ids:
        try:
            alerts = run_conflict_detection(inst_id, db)
            total += len(alerts)
        except Exception as exc:
            logger.error("Conflict scan failed for institution %s: %s", inst_id, exc, exc_info=True)

    if total:
        db.commit()

    logger.info("run_global_conflict_scan: %d new conflict alert(s) created.", total)
    return total
