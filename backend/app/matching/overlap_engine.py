"""
Overlap detection engine.

Orchestrates institution matching + complaint similarity to surface cases that
are likely related across bureaus, then creates OverlapAlert records.
"""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.matching.complaint_matcher import ComplaintMatcher, SimilarityResult
from app.matching.institution_matcher import InstitutionMatcher, MatchType
from app.models.case import Case, CaseStatus
from app.models.overlap import MatchType as DBMatchType, OverlapAlert, OverlapAlertStatus
from app.models.notification import Notification, NotificationType

logger = logging.getLogger(__name__)

# Statuses considered "active" (i.e. eligible to form an overlap pair)
_ACTIVE_STATUSES = [
    CaseStatus.received,
    CaseStatus.pending_assignment,
    CaseStatus.under_process,
    CaseStatus.awaiting_information,
    CaseStatus.transferred,
    CaseStatus.escalated,
]


# ---------------------------------------------------------------------------
# Configuration dataclass
# ---------------------------------------------------------------------------

@dataclass
class MatchConfig:
    institution_name_threshold: float = 80.0
    complaint_similarity_threshold: float = 70.0
    use_semantic: bool = False
    max_candidates: int = 100


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class OverlapCandidate:
    candidate_case: Case
    match_type: str          # "exact_id" | "institution_name_fuzzy" | "complaint_similarity"
    institution_score: float
    text_score: float
    semantic_score: Optional[float]
    combined_score: float
    evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class OverlapEngine:
    """Main pipeline: find candidates -> score -> create alerts."""

    def __init__(self, db: Session, config: Optional[MatchConfig] = None):
        self.db = db
        self.config = config or MatchConfig()
        self._inst_matcher = InstitutionMatcher()
        self._complaint_matcher = ComplaintMatcher()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def find_overlaps_for_case(self, case: Case) -> list[OverlapCandidate]:
        """Run the three-stage overlap detection pipeline for *case*."""
        candidates: list[Case] = self._find_candidate_cases(case)
        results: list[OverlapCandidate] = []

        for candidate in candidates:
            if candidate.id == case.id:
                continue

            inst_score, match_type = self._institution_score(case, candidate)
            sim_results = self._complaint_matcher.find_similar_complaints(
                case, [candidate], self.db, self.config
            )
            sim: Optional[SimilarityResult] = sim_results[0] if sim_results else None

            text_score = sim.text_score if sim else 0.0
            semantic_score = sim.semantic_score if sim else None

            # Combined score: institution match is prerequisite;
            # text similarity boosts the final score
            if inst_score > 0:
                combined = 0.6 * inst_score + 0.4 * text_score
            else:
                combined = text_score

            if combined < self.config.complaint_similarity_threshold and inst_score < self.config.institution_name_threshold:
                continue

                # Build human-readable match reasons
            match_reasons: list[str] = []
            if inst_score >= self.config.institution_name_threshold:
                if match_type == MatchType.EXACT_ID.value:
                    match_reasons.append(
                        "Exact institution match: both cases share the same AICTE Permanent ID."
                    )
                else:
                    match_reasons.append(
                        f"Institution name fuzzy match: similarity {inst_score:.1f}% "
                        f"(threshold {self.config.institution_name_threshold}%)."
                    )
            if text_score >= self.config.complaint_similarity_threshold:
                match_reasons.append(
                    f"Complaint text similarity: {text_score:.1f}% lexical overlap "
                    f"(threshold {self.config.complaint_similarity_threshold}%)."
                )
            if semantic_score is not None and semantic_score >= self.config.complaint_similarity_threshold:
                match_reasons.append(
                    f"Semantic similarity: {semantic_score:.1f}% via sentence embeddings."
                )

            # Determine detection_method label
            if match_type == MatchType.EXACT_ID.value:
                detection_method = "exact_id"
            elif semantic_score is not None and text_score > 0:
                detection_method = "combined"
            elif semantic_score is not None:
                detection_method = "semantic"
            elif text_score > 0 and inst_score < self.config.institution_name_threshold:
                detection_method = "complaint_similarity"
            else:
                detection_method = "fuzzy_name"

            evidence: dict = {
                "matched_by": [],
                "scores": {
                    "institution": inst_score,
                    "text": text_score,
                    "semantic": semantic_score,
                    "combined": combined,
                },
                "match_type": match_type,
                "match_reasons": match_reasons,
                "detection_method": detection_method,
            }
            if inst_score >= self.config.institution_name_threshold:
                evidence["matched_by"].append(match_type)
            if text_score >= self.config.complaint_similarity_threshold:
                evidence["matched_by"].append("complaint_text")

            results.append(
                OverlapCandidate(
                    candidate_case=candidate,
                    match_type=match_type,
                    institution_score=inst_score,
                    text_score=text_score,
                    semantic_score=semantic_score,
                    combined_score=combined,
                    evidence=evidence,
                )
            )

        results.sort(key=lambda c: c.combined_score, reverse=True)
        return results

    def create_overlap_alert(
        self,
        case: Case,
        candidate: OverlapCandidate,
        db: Session,
    ) -> Optional[OverlapAlert]:
        """Persist an OverlapAlert for the (case, candidate) pair.

        Returns None if a pending alert already exists for the same pair.
        """
        existing = (
            db.query(OverlapAlert)
            .filter(
                or_(
                    (OverlapAlert.case_id_incoming == case.id)
                    & (OverlapAlert.case_id_existing == candidate.candidate_case.id),
                    (OverlapAlert.case_id_incoming == candidate.candidate_case.id)
                    & (OverlapAlert.case_id_existing == case.id),
                ),
                OverlapAlert.status == OverlapAlertStatus.pending_review,
            )
            .first()
        )
        if existing:
            logger.debug(
                "Skipping duplicate overlap alert for cases %s / %s",
                case.id,
                candidate.candidate_case.id,
            )
            return None

        # Map match_type string to DB enum
        db_match_type = self._map_match_type(candidate.match_type)

        # Collect bureaus involved
        bureaus = []
        if case.bureau_id:
            bureaus.append(str(case.bureau_id))
        if candidate.candidate_case.bureau_id:
            b2 = str(candidate.candidate_case.bureau_id)
            if b2 not in bureaus:
                bureaus.append(b2)

        alert_number = f"OA-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8].upper()}"

        alert = OverlapAlert(
            alert_number=alert_number,
            case_id_incoming=case.id,
            case_id_existing=candidate.candidate_case.id,
            institution_id=case.institution_id or candidate.candidate_case.institution_id,
            match_type=db_match_type,
            match_score=candidate.combined_score,
            match_evidence=candidate.evidence,
            bureaus_involved=bureaus,
            status=OverlapAlertStatus.pending_review,
            match_reasons=candidate.evidence.get("match_reasons", []),
            detection_method=candidate.evidence.get("detection_method"),
            similarity_score=candidate.combined_score,
        )
        db.add(alert)
        db.flush()

        # Create notifications for bureau officers
        self._notify_bureaus(alert, case, candidate.candidate_case, db)

        return alert

    def run_overlap_check(
        self,
        case_id: uuid.UUID,
        db: Session,
    ) -> list[OverlapAlert]:
        """Full pipeline: fetch case -> find overlaps -> create alerts."""
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case:
            logger.warning("run_overlap_check: case %s not found", case_id)
            return []

        candidates = self.find_overlaps_for_case(case)
        created: list[OverlapAlert] = []

        for candidate in candidates:
            alert = self.create_overlap_alert(case, candidate, db)
            if alert:
                created.append(alert)

        if created:
            db.commit()

        return created

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_candidate_cases(self, case: Case) -> list[Case]:
        """Return active cases that share an institution with *case*."""
        base_q = (
            self.db.query(Case)
            .filter(Case.status.in_(_ACTIVE_STATUSES))
            .filter(Case.id != case.id)
        )

        candidate_ids: set[uuid.UUID] = set()

        # Priority 1: same institution_id
        if case.institution_id:
            same_inst = (
                base_q.filter(Case.institution_id == case.institution_id)
                .order_by(Case.created_at.desc())
                .limit(self.config.max_candidates)
                .all()
            )
            candidate_ids.update(c.id for c in same_inst)

        # Priority 2: same permanent_id via institution relationship
        if case.institution and case.institution.permanent_id and len(candidate_ids) < self.config.max_candidates:
            perm_id = case.institution.permanent_id
            from app.models.institution import Institution
            perm_cases = (
                self.db.query(Case)
                .join(Institution, Case.institution_id == Institution.id)
                .filter(Institution.permanent_id == perm_id)
                .filter(Case.status.in_(_ACTIVE_STATUSES))
                .filter(Case.id != case.id)
                .order_by(Case.created_at.desc())
                .limit(self.config.max_candidates)
                .all()
            )
            candidate_ids.update(c.id for c in perm_cases)

        # If no exact institution, try fuzzy name matching to find candidates
        if not candidate_ids and case.institution:
            fuzzy_matches = self._inst_matcher.match_by_name_fuzzy(
                case.institution.name,
                self.db,
                threshold=self.config.institution_name_threshold,
            )
            inst_ids = [inst.id for inst, _ in fuzzy_matches if inst.id != case.institution_id]
            if inst_ids:
                fuzzy_cases = (
                    base_q.filter(Case.institution_id.in_(inst_ids))
                    .order_by(Case.created_at.desc())
                    .limit(self.config.max_candidates)
                    .all()
                )
                candidate_ids.update(c.id for c in fuzzy_cases)

        if not candidate_ids:
            return []

        return (
            self.db.query(Case)
            .filter(Case.id.in_(list(candidate_ids)))
            .all()
        )

    def _institution_score(self, case: Case, candidate: Case) -> tuple[float, str]:
        """Return (score, match_type_string) for the institution pair."""
        # Exact institution id match
        if (
            case.institution_id
            and candidate.institution_id
            and case.institution_id == candidate.institution_id
        ):
            return 100.0, MatchType.EXACT_ID.value

        # Same permanent_id
        inst1 = case.institution
        inst2 = candidate.institution
        if inst1 and inst2 and inst1.permanent_id and inst2.permanent_id:
            if inst1.permanent_id == inst2.permanent_id:
                return 100.0, MatchType.EXACT_ID.value

        # Fuzzy name
        if inst1 and inst2:
            from app.matching.normalizer import normalize_institution_name
            from rapidfuzz import fuzz
            n1 = normalize_institution_name(inst1.name)
            n2 = normalize_institution_name(inst2.name)
            score = max(
                fuzz.token_sort_ratio(n1, n2),
                fuzz.partial_ratio(n1, n2),
            )
            return float(score), MatchType.INSTITUTION_NAME_FUZZY.value

        return 0.0, "no_institution_match"

    @staticmethod
    def _map_match_type(match_type_str: str) -> DBMatchType:
        mapping = {
            "exact_id": DBMatchType.exact_id,
            "institution_name_fuzzy": DBMatchType.institution_name_fuzzy,
            "institution_name_semantic": DBMatchType.institution_name_semantic,
            "complaint_similarity": DBMatchType.complaint_similarity,
        }
        return mapping.get(match_type_str, DBMatchType.combined)

    def _notify_bureaus(
        self,
        alert: OverlapAlert,
        case1: Case,
        case2: Case,
        db: Session,
    ) -> None:
        """Create overlap-alert notifications for bureau officers on both cases."""
        from app.models.user import User, UserRole

        bureau_ids = set()
        if case1.bureau_id:
            bureau_ids.add(case1.bureau_id)
        if case2.bureau_id:
            bureau_ids.add(case2.bureau_id)

        if not bureau_ids:
            return

        officers = (
            db.query(User)
            .filter(
                User.bureau_id.in_(list(bureau_ids)),
                User.role.in_([
                    UserRole.rb_officer,
                    UserRole.pgrc_officer,
                    UserRole.bureau_officer,
                ]),
                User.is_active == True,  # noqa: E712
            )
            .all()
        )

        for officer in officers:
            notif = Notification(
                user_id=officer.id,
                title="Overlap Alert Detected",
                message=(
                    f"A potential overlap has been detected between cases "
                    f"{case1.case_number} and {case2.case_number}. "
                    f"Please review alert {alert.alert_number}."
                ),
                notification_type=NotificationType.overlap_alert,
                related_entity_type="overlap_alert",
                related_entity_id=alert.id,
                is_read=False,
            )
            db.add(notif)
