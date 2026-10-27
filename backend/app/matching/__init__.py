"""
Overlap detection engine for the AICTE Complaint Dashboard.

This package provides institution name matching, complaint similarity scoring,
and the full overlap-detection pipeline that identifies when multiple bureaus
are handling complaints about the same institution.
"""
from app.matching.config import MatchingConfig
from app.matching.normalizer import (
    normalize_institution_name,
    normalize_case_reference,
    extract_tokens,
    preprocess_text_for_embedding,
)
from app.matching.overlap_engine import MatchConfig, OverlapEngine, OverlapCandidate

__all__ = [
    "MatchingConfig",
    "normalize_institution_name",
    "normalize_case_reference",
    "extract_tokens",
    "preprocess_text_for_embedding",
    "MatchConfig",
    "OverlapEngine",
    "OverlapCandidate",
]
