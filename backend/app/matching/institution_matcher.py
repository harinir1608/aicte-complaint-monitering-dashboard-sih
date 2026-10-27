"""
Institution matching — maps a raw institution name / permanent-id to a
canonical Institution record.

Two strategies are supported:
  * Exact permanent-id lookup (fastest, most reliable)
  * Fuzzy name matching via RapidFuzz (handles spelling variants, abbreviations)
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Optional

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.matching.normalizer import normalize_institution_name
from app.models.institution import Institution, InstitutionAlias


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

class MatchType(str, enum.Enum):
    EXACT_ID = "exact_id"
    INSTITUTION_NAME_FUZZY = "institution_name_fuzzy"
    NO_MATCH = "no_match"


@dataclass
class MatchResult:
    matched_institution: Optional[Institution]
    match_type: MatchType
    score: float
    evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class InstitutionMatcher:
    """Stateless helper that resolves raw institution identifiers to DB rows."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def match_by_permanent_id(
        self,
        permanent_id: str,
        db: Session,
    ) -> Optional[Institution]:
        """Return the Institution with *permanent_id* or None."""
        if not permanent_id:
            return None
        return (
            db.query(Institution)
            .filter(Institution.permanent_id == permanent_id.strip())
            .first()
        )

    def match_by_name_fuzzy(
        self,
        name: str,
        db: Session,
        threshold: float = 80.0,
    ) -> list[tuple[Institution, float]]:
        """Return institutions whose name (or alias) fuzzy-matches *name*.

        Both ``token_sort_ratio`` and ``partial_ratio`` are computed; the
        higher of the two is used as the final score.  Results are sorted
        descending by score and filtered to ``>= threshold``.
        """
        if not name:
            return []

        normalised_query = normalize_institution_name(name)
        if not normalised_query:
            return []

        institutions: list[Institution] = (
            db.query(Institution)
            .filter(Institution.is_active == True)  # noqa: E712
            .all()
        )

        # Build alias map {institution_id -> [alias_normalised, ...]}
        aliases: list[InstitutionAlias] = db.query(InstitutionAlias).all()
        alias_map: dict = {}
        for a in aliases:
            alias_map.setdefault(str(a.institution_id), []).append(
                normalize_institution_name(a.alias)
            )

        results: list[tuple[Institution, float]] = []

        for inst in institutions:
            best = self._best_score(
                normalised_query,
                normalize_institution_name(inst.name),
                alias_map.get(str(inst.id), []),
            )
            if best >= threshold:
                results.append((inst, best))

        results.sort(key=lambda x: x[1], reverse=True)
        return results

    def match_institution(
        self,
        name: str,
        permanent_id: Optional[str],
        address_hints: dict,
        db: Session,
    ) -> MatchResult:
        """Multi-stage institution resolution.

        Stage 1: exact permanent-id lookup.
        Stage 2: fuzzy name matching.
        Stage 3: no match found.
        """
        # Stage 1 — exact permanent-id
        if permanent_id:
            inst = self.match_by_permanent_id(permanent_id, db)
            if inst:
                return MatchResult(
                    matched_institution=inst,
                    match_type=MatchType.EXACT_ID,
                    score=100.0,
                    evidence={"permanent_id": permanent_id},
                )

        # Stage 2 — fuzzy name
        if name:
            fuzzy_matches = self.match_by_name_fuzzy(name, db)
            if fuzzy_matches:
                best_inst, best_score = fuzzy_matches[0]
                return MatchResult(
                    matched_institution=best_inst,
                    match_type=MatchType.INSTITUTION_NAME_FUZZY,
                    score=best_score,
                    evidence={
                        "query_name": name,
                        "matched_name": best_inst.name,
                        "score": best_score,
                        "address_hints": address_hints,
                    },
                )

        return MatchResult(
            matched_institution=None,
            match_type=MatchType.NO_MATCH,
            score=0.0,
            evidence={"query_name": name, "permanent_id": permanent_id},
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _best_score(
        query: str,
        candidate: str,
        aliases: list[str],
    ) -> float:
        """Return the highest RapidFuzz score across all name variants."""
        candidates = [candidate] + aliases
        best = 0.0
        for cand in candidates:
            if not cand:
                continue
            tsr = fuzz.token_sort_ratio(query, cand)
            pr = fuzz.partial_ratio(query, cand)
            score = max(tsr, pr)
            if score > best:
                best = score
        return best
