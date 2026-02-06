"""Initial schema.

Revision ID: 001
Create Date: 2026-02-05
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Proposals
    op.create_table(
        "proposals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("domain", sa.String(50), nullable=False),
        sa.Column("submitted_by", sa.String(255), nullable=False),
        sa.Column(
            "submitted_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column(
            "status", sa.String(50), nullable=False, server_default="draft"
        ),
        sa.Column(
            "delta_b", sa.Numeric(20, 10), nullable=False
        ),
        sa.Column(
            "delta_h", sa.Numeric(20, 10), nullable=False
        ),
        sa.Column("r", sa.Numeric(10, 10), nullable=False),
        sa.Column("s", sa.Numeric(20, 10), nullable=False),
        sa.Column("u", sa.Numeric(10, 10), nullable=False),
        sa.Column(
            "human_signoff_required", sa.Boolean, server_default="false"
        ),
        sa.Column(
            "human_signoff_obtained", sa.Boolean, server_default="false"
        ),
        sa.Column("rollback_plan", sa.Text, nullable=True),
        sa.Column("uncertainty_explanation", sa.Text, nullable=True),
        sa.Column(
            "stakeholder_impacts",
            postgresql.JSONB,
            server_default="[]",
        ),
        sa.Column("tags", postgresql.JSONB, server_default="[]"),
        sa.CheckConstraint("delta_b >= 0", name="ck_proposals_delta_b"),
        sa.CheckConstraint("delta_h > 0", name="ck_proposals_delta_h"),
        sa.CheckConstraint(
            "r >= 0 AND r <= 1", name="ck_proposals_r_range"
        ),
        sa.CheckConstraint("s > 0", name="ck_proposals_s_positive"),
        sa.CheckConstraint(
            "u >= 0 AND u <= 1", name="ck_proposals_u_range"
        ),
    )
    op.create_index("ix_proposals_status", "proposals", ["status"])
    op.create_index(
        "ix_proposals_submitted_at", "proposals", ["submitted_at"]
    )
    op.create_index("ix_proposals_domain", "proposals", ["domain"])

    # Evaluations
    op.create_table(
        "evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "proposal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proposals.id"),
            nullable=False,
        ),
        sa.Column(
            "evaluated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("decision", sa.String(50), nullable=False),
        sa.Column("snapshot_delta_b", sa.Numeric(20, 10), nullable=False),
        sa.Column("snapshot_delta_h", sa.Numeric(20, 10), nullable=False),
        sa.Column("snapshot_r", sa.Numeric(10, 10), nullable=False),
        sa.Column("snapshot_s", sa.Numeric(20, 10), nullable=False),
        sa.Column("snapshot_u", sa.Numeric(10, 10), nullable=False),
        sa.Column("snapshot_index", sa.Numeric(20, 10), nullable=False),
        sa.Column(
            "snapshot_growth_permitted", sa.Boolean, nullable=False
        ),
        sa.Column(
            "pipeline_stages", postgresql.JSONB, server_default="[]"
        ),
        sa.Column(
            "test_class_results", postgresql.JSONB, server_default="[]"
        ),
        sa.Column("violations", postgresql.JSONB, server_default="[]"),
        sa.Column("gate_conditions_met", sa.Boolean, nullable=False),
        sa.Column("firmware_allow_growth", sa.Boolean, nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("total_duration_ms", sa.Numeric(10, 3), nullable=False),
    )
    op.create_index(
        "ix_evaluations_proposal_id", "evaluations", ["proposal_id"]
    )
    op.create_index(
        "ix_evaluations_decision", "evaluations", ["decision"]
    )
    op.create_index(
        "ix_evaluations_evaluated_at", "evaluations", ["evaluated_at"]
    )

    # Compliance reports
    op.create_table(
        "compliance_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "proposal_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("proposals.id"),
            nullable=False,
        ),
        sa.Column(
            "evaluation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evaluations.id"),
            nullable=True,
        ),
        sa.Column(
            "generated_at", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("is_compliant", sa.Boolean, nullable=False),
        sa.Column("violations", postgresql.JSONB, server_default="[]"),
        sa.Column(
            "institutional_diagnoses",
            postgresql.JSONB,
            server_default="[]",
        ),
        sa.Column(
            "bodhisattva_index", sa.Numeric(20, 10), nullable=False
        ),
        sa.Column("summary", sa.Text, nullable=False),
    )
    op.create_index(
        "ix_compliance_proposal_id",
        "compliance_reports",
        ["proposal_id"],
    )
    op.create_index(
        "ix_compliance_is_compliant",
        "compliance_reports",
        ["is_compliant"],
    )

    # Audit log (append-only)
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "timestamp", sa.DateTime(timezone=True), nullable=False
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("actor", sa.String(255), nullable=False),
        sa.Column(
            "proposal_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column(
            "evaluation_id", postgresql.UUID(as_uuid=True), nullable=True
        ),
        sa.Column("details", postgresql.JSONB, server_default="{}"),
        sa.Column(
            "bodhisattva_index", sa.Numeric(20, 10), nullable=True
        ),
        sa.Column("growth_permitted", sa.Boolean, nullable=True),
    )
    op.create_index("ix_audit_timestamp", "audit_log", ["timestamp"])
    op.create_index("ix_audit_action", "audit_log", ["action"])
    op.create_index("ix_audit_proposal_id", "audit_log", ["proposal_id"])
    op.create_index("ix_audit_actor", "audit_log", ["actor"])

    # Append-only protection for audit_log
    op.execute(
        "CREATE RULE audit_log_no_update AS ON UPDATE TO audit_log "
        "DO INSTEAD NOTHING;"
    )
    op.execute(
        "CREATE RULE audit_log_no_delete AS ON DELETE TO audit_log "
        "DO INSTEAD NOTHING;"
    )


def downgrade() -> None:
    op.execute("DROP RULE IF EXISTS audit_log_no_delete ON audit_log;")
    op.execute("DROP RULE IF EXISTS audit_log_no_update ON audit_log;")
    op.drop_table("audit_log")
    op.drop_table("compliance_reports")
    op.drop_table("evaluations")
    op.drop_table("proposals")
