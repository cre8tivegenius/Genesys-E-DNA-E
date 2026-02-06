"""
SQLAlchemy ORM models for PostgreSQL persistence.

Tables:
- proposals: Growth proposals
- evaluations: Evaluation results with invariant snapshots
- compliance_reports: Regulatory compliance reports
- audit_log: Immutable append-only audit trail
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ProposalRow(Base):
    __tablename__ = "proposals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(50), nullable=False)
    submitted_by: Mapped[str] = mapped_column(String(255), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="draft"
    )

    # Core invariant inputs
    delta_b: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False
    )
    delta_h: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False
    )
    r: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=10), nullable=False
    )
    s: Mapped[float] = mapped_column(
        Numeric(precision=20, scale=10), nullable=False
    )
    u: Mapped[float] = mapped_column(
        Numeric(precision=10, scale=10), nullable=False
    )

    # Context
    human_signoff_required: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    human_signoff_obtained: Mapped[bool] = mapped_column(
        Boolean, default=False
    )
    rollback_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    uncertainty_explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
    stakeholder_impacts: Mapped[dict] = mapped_column(JSONB, default=list)
    tags: Mapped[list] = mapped_column(JSONB, default=list)

    # Relationships
    evaluations: Mapped[list["EvaluationRow"]] = relationship(
        back_populates="proposal"
    )

    __table_args__ = (
        CheckConstraint(
            "delta_b >= 0", name="ck_proposals_delta_b_non_negative"
        ),
        CheckConstraint(
            "delta_h > 0", name="ck_proposals_delta_h_positive"
        ),
        CheckConstraint(
            "r >= 0 AND r <= 1", name="ck_proposals_r_range"
        ),
        CheckConstraint("s > 0", name="ck_proposals_s_positive"),
        CheckConstraint(
            "u >= 0 AND u <= 1", name="ck_proposals_u_range"
        ),
        Index("ix_proposals_status", "status"),
        Index("ix_proposals_submitted_at", "submitted_at"),
        Index("ix_proposals_domain", "domain"),
    )


class EvaluationRow(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False
    )
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # Decision
    decision: Mapped[str] = mapped_column(String(50), nullable=False)

    # Invariant snapshot (denormalized for immutability)
    snapshot_delta_b: Mapped[float] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    snapshot_delta_h: Mapped[float] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    snapshot_r: Mapped[float] = mapped_column(
        Numeric(10, 10), nullable=False
    )
    snapshot_s: Mapped[float] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    snapshot_u: Mapped[float] = mapped_column(
        Numeric(10, 10), nullable=False
    )
    snapshot_index: Mapped[float] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    snapshot_growth_permitted: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )

    # Detailed results
    pipeline_stages: Mapped[dict] = mapped_column(JSONB, default=list)
    test_class_results: Mapped[dict] = mapped_column(JSONB, default=list)
    violations: Mapped[list] = mapped_column(JSONB, default=list)

    # Gate
    gate_conditions_met: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    firmware_allow_growth: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )

    # Audit
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    total_duration_ms: Mapped[float] = mapped_column(
        Numeric(10, 3), nullable=False
    )

    # Relationships
    proposal: Mapped["ProposalRow"] = relationship(
        back_populates="evaluations"
    )

    __table_args__ = (
        Index("ix_evaluations_proposal_id", "proposal_id"),
        Index("ix_evaluations_decision", "decision"),
        Index("ix_evaluations_evaluated_at", "evaluated_at"),
    )


class ComplianceReportRow(Base):
    __tablename__ = "compliance_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    proposal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("proposals.id"), nullable=False
    )
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("evaluations.id"), nullable=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    is_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False)
    violations: Mapped[dict] = mapped_column(JSONB, default=list)
    institutional_diagnoses: Mapped[dict] = mapped_column(
        JSONB, default=list
    )
    bodhisattva_index: Mapped[float] = mapped_column(
        Numeric(20, 10), nullable=False
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)

    __table_args__ = (
        Index("ix_compliance_proposal_id", "proposal_id"),
        Index("ix_compliance_is_compliant", "is_compliant"),
    )


class AuditLogRow(Base):
    """Immutable, append-only audit log."""

    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor: Mapped[str] = mapped_column(String(255), nullable=False)

    # References
    proposal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    evaluation_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Full details
    details: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Invariant state at time of action
    bodhisattva_index: Mapped[float | None] = mapped_column(
        Numeric(20, 10), nullable=True
    )
    growth_permitted: Mapped[bool | None] = mapped_column(
        Boolean, nullable=True
    )

    __table_args__ = (
        Index("ix_audit_timestamp", "timestamp"),
        Index("ix_audit_action", "action"),
        Index("ix_audit_proposal_id", "proposal_id"),
        Index("ix_audit_actor", "actor"),
    )
