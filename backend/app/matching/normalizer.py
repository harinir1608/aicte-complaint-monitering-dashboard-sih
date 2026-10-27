"""
Text normalisation helpers for institution names and case references.

All functions are pure (no DB access) and can be called from any layer.
"""
from __future__ import annotations

import re


# ---------------------------------------------------------------------------
# Abbreviation expansion table for institution names
# ---------------------------------------------------------------------------

_ABBREV_EXPANSIONS: list[tuple[str, str]] = [
    # Ordered longest-match-first inside each group
    (r"\binst\b\.?", "institute"),
    (r"\bengg\b\.?", "engineering"),
    (r"\btech\b\.?", "technology"),
    (r"\bcol\b\.?", "college"),
    (r"\bmgmt\b\.?", "management"),
    (r"\bpharmcy\b", "pharmacy"),
    (r"\bpharma\b", "pharmacy"),
    (r"\bpolytec\b", "polytechnic"),
    (r"\bpoly\b", "polytechnic"),
    (r"\buniv\b\.?", "university"),
    (r"\bsci\b\.?", "science"),
    (r"\beduc\b\.?", "education"),
    (r"\bacad\b\.?", "academy"),
]

# Suffixes that carry no identifying information and should be removed
_NOISE_SUFFIXES: tuple[str, ...] = (
    r"\(autonomous\)",
    r"\bautonomous\b",
    r"\bpvt\b\.?",
    r"\bltd\b\.?",
    r"\btrust\b",
    r"\bsociety\b",
)


def normalize_institution_name(name: str) -> str:
    """Return a canonical lower-case form of an institution name.

    Steps applied in order:
    1. Lowercase and strip leading/trailing whitespace.
    2. Expand common abbreviations.
    3. Strip noise suffixes.
    4. Remove special characters (keep letters, digits, spaces).
    5. Collapse multiple spaces.
    """
    if not name:
        return ""

    text = name.lower().strip()

    # Expand abbreviations
    for pattern, replacement in _ABBREV_EXPANSIONS:
        text = re.sub(pattern, replacement, text)

    # Remove noise suffixes
    for pattern in _NOISE_SUFFIXES:
        text = re.sub(pattern, " ", text)

    # Remove special characters (keep alphanumeric and spaces)
    text = re.sub(r"[^a-z0-9 ]", " ", text)

    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_case_reference(ref: str) -> str:
    """Return an upper-case alphanumeric-only representation of a case/complaint reference.

    Example: ``"AICTE/2024-PGRC/001"`` -> ``"AICTE2024PGRC001"``
    """
    if not ref:
        return ""
    text = ref.upper()
    text = re.sub(r"[^A-Z0-9]", "", text)
    return text


def extract_tokens(text: str) -> list[str]:
    """Split *text* into lowercase alphabetic/numeric tokens.

    Tokens shorter than 2 characters are discarded to reduce noise.
    """
    if not text:
        return []
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return [w for w in words if len(w) >= 2]


def preprocess_text_for_embedding(text: str) -> str:
    """Lightly clean text before feeding it to a sentence-transformer model.

    Preserves sentence structure (punctuation, casing) but removes control
    characters and collapses excessive whitespace.
    """
    if not text:
        return ""
    # Remove control characters
    text = re.sub(r"[\x00-\x1f\x7f]", " ", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    # Truncate to 512 chars — most embedding models cap at 512 tokens
    return text[:512]
