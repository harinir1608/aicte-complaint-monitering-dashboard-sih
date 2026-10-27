"""Add overlap explainability columns and conflict_alerts table

Revision ID: 002
Revises: 001
Create Date: 2026-10-27 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── overlap_alerts: explainability columns ────────────────────────────────
    op.add_column(
        "overlap_alerts",
        sa.Column("match_reasons", postgresql.JSON(astext_type=sa.Text()), nullable=True),
    )
    op.add_column(
        "overlap_alerts",
        sa.Column("detection_method", sa.String(50), nullable=True),
    )
    op.add_column(
        "overlap_alerts",
        sa.Column("similarity_score", sa.Float(), nullable=True),
    )

    # ── conflict_severity_enum ────────────────────────────────────────────────
    conflict_severity_enum = sa.Enum("low", "medium", "high", name="conflict_severity_enum")
    conflict_severity_enum.create(op.get_bind(), checkfirst=True)

    # ── conflict_status_enum ──────────────────────────────────────────────────
    conflict_status_enum = sa.Enum(
        "open", "acknowledged", "resolved", "dismissed",
        name="conflict_status_enum",
    )
    conflict_status_enum.create(op.get_bind(), checkfirst=True)

    # ── conflict_alerts table ─────────────────────────────────────────────────
    op.create_table(
        "conflict_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "institution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("institutions.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("case_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("bureau_ids", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("rule_triggered", sa.String(200), nullable=False),
        sa.Column("rule_description", sa.Text(), nullable=True),
        sa.Column("evidence", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "severity",
            sa.Enum("low", "medium", "high", name="conflict_severity_enum"),
            nullable=False,
        ),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column(
            "coordination_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum("open", "acknowledged", "resolved", "dismissed", name="conflict_status_enum"),
            nullable=False,
            server_default="open",
        ),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column(
            "resolved_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("conflict_alerts")
    op.execute("DROP TYPE IF EXISTS conflict_status_enum")
    op.execute("DROP TYPE IF EXISTS conflict_severity_enum")
    op.drop_column("overlap_alerts", "similarity_score")
    op.drop_column("overlap_alerts", "detection_method")
    op.drop_column("overlap_alerts", "match_reasons")
