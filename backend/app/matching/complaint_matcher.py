"""
Complaint text similarity — lexical (RapidFuzz) and optional semantic
(sentence-transformers) matching.

Semantic matching is guarded behind a try/except ImportError so the service
starts successfully even when sentence-transformers is not installed.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from rapidfuzz import fuzz
from sqlalchemy.orm import Session

from app.matching.normalizer import preprocess_text_for_embedding

if TYPE_CHECKING:
    from app.models.case import Case
    from app.matching.overlap_engine import MatchConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional sentence-transformers import
# ---------------------------------------------------------------------------

SEMANTIC_AVAILABLE = False
_sentence_model = None

try:
    _ENABLE_SEMANTIC = os.getenv("ENABLE_SEMANTIC_MATCHING", "false").lower() == "true"
    if _ENABLE_SEMANTIC:
        from sentence_transformers import SentenceTransformer  # type: ignore
        import numpy as np  # type: ignore
        SEMANTIC_AVAILABLE = True
        logger.info("sentence-transformers available; semantic matching enabled.")
    else:
        logger.debug("ENABLE_SEMANTIC_MATCHING=false — skipping model load.")
except ImportError:
    logger.warning(
        "sentence-transformers not installed — semantic matching disabled. "
        "Install it and set ENABLE_SEMANTIC_MATCHING=true to enable."
    )


def _get_semantic_model():
    """Lazy-load the sentence-transformer model on first use."""
    global _sentence_model
    if _sentence_model is None and SEMANTIC_AVAILABLE:
        model_name = os.getenv("SEMANTIC_MODEL_NAME", "all-MiniLM-L6-v2")
        from sentence_transformers import SentenceTransformer  # type: ignore
        _sentence_model = SentenceTransformer(model_name)
        logger.info("Loaded semantic model: %s", model_name)
    return _sentence_model


# ---------------------------------------------------------------------------
# Value objects
# ---------------------------------------------------------------------------

@dataclass
class SimilarityResult:
    candidate_case_id: str
    text_score: float
    semantic_score: Optional[float]
    combined_score: float
    evidence: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Matcher
# ---------------------------------------------------------------------------

class ComplaintMatcher:
    """Stateless helper that compares complaint texts for similarity."""

    def compare_complaints_text(self, text1: str, text2: str) -> float:
        """Lexical similarity using RapidFuzz token_set_ratio.

        Returns a score in [0.0, 100.0].
        """
        if not text1 or not text2:
            return 0.0
        return float(fuzz.token_set_ratio(text1, text2))

    def compare_complaints_semantic(
        self, text1: str, text2: str
    ) -> Optional[float]:
        """Cosine similarity via sentence-transformers, scaled to [0, 100].

        Returns None if semantic matching is unavailable or disabled.
        """
        if not SEMANTIC_AVAILABLE:
            return None
        try:
            import numpy as np  # type: ignore

            model = _get_semantic_model()
            if model is None:
                return None

            t1 = preprocess_text_for_embedding(text1)
            t2 = preprocess_text_for_embedding(text2)
            if not t1 or not t2:
                return None

            embeddings = model.encode([t1, t2], convert_to_numpy=True)
            # Cosine similarity
            v1, v2 = embeddings[0], embeddings[1]
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm == 0:
                return 0.0
            cosine = float(np.dot(v1, v2) / norm)
            # Clamp to [0, 1] then scale to [0, 100]
            return max(0.0, min(cosine, 1.0)) * 100.0
        except Exception as exc:
            logger.warning("Semantic comparison failed: %s", exc)
            return None

    def find_similar_complaints(
        self,
        new_case: "Case",
        candidate_cases: "list[Case]",
        db: Session,
        config: "MatchConfig",
    ) -> "list[SimilarityResult]":
        """Score *new_case* against each candidate and return matches above threshold.

        The combined score is a weighted blend:
          - If semantic available: 40% text + 60% semantic
          - Else: 100% text score
        """
        new_text = self._case_text(new_case)
        results: list[SimilarityResult] = []

        for candidate in candidate_cases:
            cand_text = self._case_text(candidate)

            text_score = self.compare_complaints_text(new_text, cand_text)
            semantic_score = (
                self.compare_complaints_semantic(new_text, cand_text)
                if config.use_semantic
                else None
            )

            if semantic_score is not None:
                combined = 0.4 * text_score + 0.6 * semantic_score
            else:
                combined = text_score

            if combined >= config.complaint_similarity_threshold:
                results.append(
                    SimilarityResult(
                        candidate_case_id=str(candidate.id),
                        text_score=text_score,
                        semantic_score=semantic_score,
                        combined_score=combined,
                        evidence={
                            "text_score": text_score,
                            "semantic_score": semantic_score,
                            "new_case_text_preview": new_text[:200],
                            "candidate_text_preview": cand_text[:200],
                        },
                    )
                )

        results.sort(key=lambda r: r.combined_score, reverse=True)
        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _case_text(case: "Case") -> str:
        subject = case.subject or ""
        description = case.description or ""
        return f"{subject} {description}".strip()
