"""
Database models package.

Import order matters: Base must be imported first so all models
register themselves on the same metadata instance.
"""
from .base import Base, TimestampMixin, UUIDMixin
from .bureau import Bureau, Region
from .user import User, UserRole
from .institution import Institution, InstitutionAlias, InstitutionType, AliasType
from .complaint import (
    Complaint,
    ComplaintCategory,
    ComplaintDocument,
    ComplaintSource,
    ComplaintStatus,
    ComplaintPriority,
)
from .case import (
    Case,
    CaseAssignment,
    CaseAction,
    CaseDocument,
    RelatedCase,
    CaseStatus,
    CasePriority,
    CaseActionType,
    RelationshipType,
)
from .overlap import (
    OverlapAlert,
    OverlapReview,
    MatchType,
    OverlapAlertStatus,
    OverlapReviewDecision,
)
from .notification import Notification, SLARule, NotificationType
from .audit import AuditLog
from .conflict import ConflictAlert, ConflictSeverity, ConflictStatus

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    # Bureau
    "Bureau",
    "Region",
    # User
    "User",
    "UserRole",
    # Institution
    "Institution",
    "InstitutionAlias",
    "InstitutionType",
    "AliasType",
    # Complaint
    "Complaint",
    "ComplaintCategory",
    "ComplaintDocument",
    "ComplaintSource",
    "ComplaintStatus",
    "ComplaintPriority",
    # Case
    "Case",
    "CaseAssignment",
    "CaseAction",
    "CaseDocument",
    "RelatedCase",
    "CaseStatus",
    "CasePriority",
    "CaseActionType",
    "RelationshipType",
    # Overlap
    "OverlapAlert",
    "OverlapReview",
    "MatchType",
    "OverlapAlertStatus",
    "OverlapReviewDecision",
    # Notification
    "Notification",
    "SLARule",
    "NotificationType",
    # Audit
    "AuditLog",
    # Conflict
    "ConflictAlert",
    "ConflictSeverity",
    "ConflictStatus",
]
