"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union
import uuid

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enums ─────────────────────────────────────────────────────────────────
    user_role_enum = sa.Enum(
        "system_admin", "rb_officer", "pgrc_officer", "bureau_officer",
        "regional_officer", "senior_management",
        name="user_role_enum",
    )
    institution_type_enum = sa.Enum(
        "engineering", "pharmacy", "management", "polytechnic", "architecture", "other",
        name="institution_type_enum",
    )
    alias_type_enum = sa.Enum(
        "abbreviation", "former_name", "colloquial", "other",
        name="alias_type_enum",
    )
    complaint_source_enum = sa.Enum(
        "email", "portal", "letter", "phone", "walk_in",
        "ministry_reference", "court", "rti", "other",
        name="complaint_source_enum",
    )
    complaint_status_enum = sa.Enum(
        "received", "pending_assignment", "under_process", "awaiting_information",
        "transferred", "escalated", "disposed", "closed",
        name="complaint_status_enum",
    )
    complaint_priority_enum = sa.Enum(
        "low", "normal", "high", "urgent", "critical",
        name="complaint_priority_enum",
    )
    case_status_enum = sa.Enum(
        "received", "pending_assignment", "under_process", "awaiting_information",
        "transferred", "escalated", "disposed", "closed",
        name="case_status_enum",
    )
    case_priority_enum = sa.Enum(
        "low", "normal", "high", "urgent", "critical",
        name="case_priority_enum",
    )
    case_action_type_enum = sa.Enum(
        "note", "status_change", "assignment", "transfer", "escalation",
        "document_upload", "decision", "reminder", "other",
        name="case_action_type_enum",
    )
    relationship_type_enum = sa.Enum(
        "same_institution", "same_complaint", "similar_issue",
        "escalation", "transfer", "other",
        name="relationship_type_enum",
    )
    match_type_enum = sa.Enum(
        "exact_id", "exact_reference", "institution_name_fuzzy",
        "institution_name_semantic", "complaint_similarity", "combined",
        name="match_type_enum",
    )
    overlap_alert_status_enum = sa.Enum(
        "pending_review", "confirmed_related", "false_positive", "linked", "dismissed",
        name="overlap_alert_status_enum",
    )
    overlap_review_decision_enum = sa.Enum(
        "confirmed_related", "false_positive", "linked",
        "maintain_separate", "needs_investigation",
        name="overlap_review_decision_enum",
    )
    notification_type_enum = sa.Enum(
        "assignment", "deadline_approaching", "overdue", "overlap_alert",
        "transfer", "escalation", "system",
        name="notification_type_enum",
    )

    # Create all enums
    for enum in [
        user_role_enum, institution_type_enum, alias_type_enum,
        complaint_source_enum, complaint_status_enum, complaint_priority_enum,
        case_status_enum, case_priority_enum, case_action_type_enum,
        relationship_type_enum, match_type_enum, overlap_alert_status_enum,
        overlap_review_decision_enum, notification_type_enum,
    ]:
        enum.create(op.get_bind(), checkfirst=True)

    # ── bureaus ───────────────────────────────────────────────────────────────
    op.create_table(
        "bureaus",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_bureaus_code", "bureaus", ["code"])

    # ── regions ───────────────────────────────────────────────────────────────
    op.create_table(
        "regions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("states", postgresql.JSON, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_regions_code", "regions", ["code"])

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("employee_id", sa.String(100), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_superuser", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("bureau_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bureaus.id", ondelete="SET NULL"), nullable=True),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("last_login", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_employee_id", "users", ["employee_id"])
    op.create_index("ix_users_bureau_id", "users", ["bureau_id"])
    op.create_index("ix_users_region_id", "users", ["region_id"])

    # ── institutions ──────────────────────────────────────────────────────────
    op.create_table(
        "institutions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("permanent_id", sa.String(100), nullable=True, unique=True),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column("region_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("regions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("institution_type", institution_type_enum, nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("pin_code", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("website", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_institutions_permanent_id", "institutions", ["permanent_id"])
    op.create_index("ix_institutions_name", "institutions", ["name"])
    op.create_index("ix_institutions_region_id", "institutions", ["region_id"])

    # ── institution_aliases ───────────────────────────────────────────────────
    op.create_table(
        "institution_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(500), nullable=False),
        sa.Column("alias_type", alias_type_enum, nullable=False),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_institution_aliases_institution_id", "institution_aliases", ["institution_id"])

    # ── complaint_categories ──────────────────────────────────────────────────
    op.create_table(
        "complaint_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("default_sla_days", sa.Integer, nullable=True),
    )
    op.create_index("ix_complaint_categories_code", "complaint_categories", ["code"])

    # ── complaints ────────────────────────────────────────────────────────────
    op.create_table(
        "complaints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("complaint_number", sa.String(50), nullable=False, unique=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("institution_name_raw", sa.Text, nullable=True),
        sa.Column("source", complaint_source_enum, nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaint_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("received_date", sa.Date, nullable=False),
        sa.Column("complainant_name", sa.String(200), nullable=True),
        sa.Column("complainant_contact", sa.String(200), nullable=True),
        sa.Column("is_anonymous", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("bureau_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bureaus.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", complaint_status_enum, nullable=False, server_default="received"),
        sa.Column("priority", complaint_priority_enum, nullable=False, server_default="normal"),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_complaints_complaint_number", "complaints", ["complaint_number"])
    op.create_index("ix_complaints_institution_id", "complaints", ["institution_id"])
    op.create_index("ix_complaints_bureau_id", "complaints", ["bureau_id"])
    op.create_index("ix_complaints_category_id", "complaints", ["category_id"])

    # ── complaint_documents ───────────────────────────────────────────────────
    op.create_table(
        "complaint_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("content_type", sa.String(200), nullable=True),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_complaint_documents_complaint_id", "complaint_documents", ["complaint_id"])

    # ── cases ─────────────────────────────────────────────────────────────────
    op.create_table(
        "cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("case_number", sa.String(50), nullable=False, unique=True),
        sa.Column("complaint_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaints.id", ondelete="SET NULL"), nullable=True),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("bureau_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bureaus.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaint_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", case_status_enum, nullable=False, server_default="received"),
        sa.Column("priority", case_priority_enum, nullable=False, server_default="normal"),
        sa.Column("sla_days", sa.Integer, nullable=True),
        sa.Column("expected_disposal_date", sa.Date, nullable=True),
        sa.Column("disposal_date", sa.Date, nullable=True),
        sa.Column("disposal_remarks", sa.Text, nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_cases_case_number", "cases", ["case_number"])
    op.create_index("ix_cases_complaint_id", "cases", ["complaint_id"])
    op.create_index("ix_cases_institution_id", "cases", ["institution_id"])
    op.create_index("ix_cases_bureau_id", "cases", ["bureau_id"])
    op.create_index("ix_cases_category_id", "cases", ["category_id"])

    # ── case_assignments ──────────────────────────────────────────────────────
    op.create_table(
        "case_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_to_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="true"),
    )
    op.create_index("ix_case_assignments_case_id", "case_assignments", ["case_id"])

    # ── case_actions ──────────────────────────────────────────────────────────
    op.create_table(
        "case_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action_type", case_action_type_enum, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("performed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("old_status", sa.String(50), nullable=True),
        sa.Column("new_status", sa.String(50), nullable=True),
        sa.Column("metadata", postgresql.JSON, nullable=True),
    )
    op.create_index("ix_case_actions_case_id", "case_actions", ["case_id"])

    # ── case_documents ────────────────────────────────────────────────────────
    op.create_table(
        "case_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("case_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("storage_key", sa.String(1000), nullable=False),
        sa.Column("file_size", sa.Integer, nullable=True),
        sa.Column("content_type", sa.String(200), nullable=True),
        sa.Column("uploaded_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_case_documents_case_id", "case_documents", ["case_id"])

    # ── related_cases ─────────────────────────────────────────────────────────
    op.create_table(
        "related_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("case_id_1", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id_2", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", relationship_type_enum, nullable=False),
        sa.Column("rationale", sa.Text, nullable=True),
        sa.Column("linked_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("linked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("coordination_notes", sa.Text, nullable=True),
    )
    op.create_index("ix_related_cases_case_id_1", "related_cases", ["case_id_1"])
    op.create_index("ix_related_cases_case_id_2", "related_cases", ["case_id_2"])

    # ── overlap_alerts ────────────────────────────────────────────────────────
    op.create_table(
        "overlap_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("alert_number", sa.String(50), nullable=False, unique=True),
        sa.Column("case_id_incoming", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("case_id_existing", postgresql.UUID(as_uuid=True), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("institution_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("institutions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("match_type", match_type_enum, nullable=False),
        sa.Column("match_score", sa.Float, nullable=True),
        sa.Column("match_evidence", postgresql.JSON, nullable=True),
        sa.Column("bureaus_involved", postgresql.JSON, nullable=True),
        sa.Column("status", overlap_alert_status_enum, nullable=False, server_default="pending_review"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_overlap_alerts_alert_number", "overlap_alerts", ["alert_number"])
    op.create_index("ix_overlap_alerts_case_id_incoming", "overlap_alerts", ["case_id_incoming"])
    op.create_index("ix_overlap_alerts_case_id_existing", "overlap_alerts", ["case_id_existing"])
    op.create_index("ix_overlap_alerts_institution_id", "overlap_alerts", ["institution_id"])

    # ── overlap_reviews ───────────────────────────────────────────────────────
    op.create_table(
        "overlap_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("alert_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("overlap_alerts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reviewed_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("decision", overlap_review_decision_enum, nullable=False),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column("coordination_owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_overlap_reviews_alert_id", "overlap_reviews", ["alert_id"])

    # ── notifications ─────────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("notification_type", notification_type_enum, nullable=False),
        sa.Column("related_entity_type", sa.String(100), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    # ── sla_rules ─────────────────────────────────────────────────────────────
    op.create_table(
        "sla_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("bureau_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("bureaus.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("complaint_categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("priority", sa.String(50), nullable=True),
        sa.Column("sla_days", sa.Integer, nullable=False, server_default="30"),
        sa.Column("warning_days", sa.Integer, nullable=False, server_default="5"),
        sa.Column("escalation_days", sa.Integer, nullable=False, server_default="2"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sla_rules_bureau_id", "sla_rules", ["bureau_id"])
    op.create_index("ix_sla_rules_category_id", "sla_rules", ["category_id"])

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_email", sa.String(255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("old_value", postgresql.JSON, nullable=True),
        sa.Column("new_value", postgresql.JSON, nullable=True),
        sa.Column("remarks", sa.Text, nullable=True),
        sa.Column("request_id", sa.String(100), nullable=True),
        sa.Column("ip_address", sa.String(50), nullable=True),
    )
    op.create_index("ix_audit_logs_entity_type", "audit_logs", ["entity_type"])
    op.create_index("ix_audit_logs_entity_id", "audit_logs", ["entity_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("sla_rules")
    op.drop_table("notifications")
    op.drop_table("overlap_reviews")
    op.drop_table("overlap_alerts")
    op.drop_table("related_cases")
    op.drop_table("case_documents")
    op.drop_table("case_actions")
    op.drop_table("case_assignments")
    op.drop_table("cases")
    op.drop_table("complaint_documents")
    op.drop_table("complaints")
    op.drop_table("complaint_categories")
    op.drop_table("institution_aliases")
    op.drop_table("institutions")
    op.drop_table("users")
    op.drop_table("regions")
    op.drop_table("bureaus")

    for enum_name in [
        "notification_type_enum",
        "overlap_review_decision_enum",
        "overlap_alert_status_enum",
        "match_type_enum",
        "relationship_type_enum",
        "case_action_type_enum",
        "case_priority_enum",
        "case_status_enum",
        "complaint_priority_enum",
        "complaint_status_enum",
        "complaint_source_enum",
        "alias_type_enum",
        "institution_type_enum",
        "user_role_enum",
    ]:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
