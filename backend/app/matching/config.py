"""
Matching configuration loaded from environment variables.

All thresholds and toggles can be overridden via env vars so that
production / test environments can tune behaviour without code changes.
"""
from __future__ import annotations

import os


class MatchingConfig:
    """Centralised configuration for the overlap-detection engine."""

    # Institution name similarity threshold (RapidFuzz score 0-100)
    INSTITUTION_NAME_THRESHOLD: float = float(
        os.getenv("INSTITUTION_NAME_THRESHOLD", "80.0")
    )

    # Text similarity threshold for complaint description comparison
    COMPLAINT_SIMILARITY_THRESHOLD: float = float(
        os.getenv("COMPLAINT_SIMILARITY_THRESHOLD", "70.0")
    )

    # Enable sentence-transformer semantic matching.
    # Deliberately off by default so the ~400 MB model is not downloaded
    # automatically in CI / lightweight environments.
    ENABLE_SEMANTIC_MATCHING: bool = (
        os.getenv("ENABLE_SEMANTIC_MATCHING", "false").lower() == "true"
    )

    # Maximum number of candidate cases to evaluate per run
    MAX_CANDIDATES: int = int(os.getenv("OVERLAP_MAX_CANDIDATES", "100"))

    # Sentence-transformer model name (used when semantic matching is enabled)
    SEMANTIC_MODEL_NAME: str = os.getenv(
        "SEMANTIC_MODEL_NAME", "all-MiniLM-L6-v2"
    )

    # Warning days before SLA deadline triggers a notification
    SLA_WARNING_DAYS: int = int(os.getenv("SLA_WARNING_DAYS", "5"))
