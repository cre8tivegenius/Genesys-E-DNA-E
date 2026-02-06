"""Data access layer (CRUD operations)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bodhisattva.core.types import ProposalDomain, ProposalStatus
from bodhisattva.db.models import (
    AuditLogRow,
    ComplianceReportRow,
    EvaluationRow,
    ProposalRow,
)
from bodhisattva.models.compliance import ComplianceReport
from bodhisattva.models.evaluation import (
    EvaluationResult,
    InvariantSnapshot,
    PipelineStageResult,
    TestClassResult,
)
from bodhisattva.models.proposal import GrowthProposal


class Repository:
    """Async data access layer for all persistence operations."""

    def __init__(self, session: AsyncSession):
        self._session = session

    # --- Proposals ---

    async def save_proposal(self, proposal: GrowthProposal) -> GrowthProposal:
        row = ProposalRow(
            id=proposal.id,
            title=proposal.title,
            description=proposal.description,
            domain=proposal.domain.value,
            submitted_by=proposal.submitted_by,
            submitted_at=proposal.submitted_at,
            status=proposal.status.value,
            delta_b=float(proposal.delta_b),
            delta_h=float(proposal.delta_h),
            r=float(proposal.r),
            s=float(proposal.s),
            u=float(proposal.u),
            human_signoff_required=proposal.human_signoff_required,
            human_signoff_obtained=proposal.human_signoff_obtained,
            rollback_plan=proposal.rollback_plan,
            uncertainty_explanation=proposal.uncertainty_explanation,
            stakeholder_impacts=[
                si.model_dump(mode="json")
                for si in proposal.stakeholder_impacts
            ],
            tags=proposal.tags,
        )
        self._session.add(row)
        await self._session.commit()
        return proposal

    async def get_proposal(
        self, proposal_id: uuid.UUID
    ) -> Optional[GrowthProposal]:
        result = await self._session.execute(
            select(ProposalRow).where(ProposalRow.id == proposal_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return self._row_to_proposal(row)

    async def list_proposals(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[GrowthProposal]:
        stmt = select(ProposalRow).order_by(
            ProposalRow.submitted_at.desc()
        )
        if status:
            stmt = stmt.where(ProposalRow.status == status)
        if domain:
            stmt = stmt.where(ProposalRow.domain == domain)
        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_proposal(r) for r in rows]

    async def update_proposal_status(
        self, proposal_id: uuid.UUID, status: ProposalStatus
    ) -> Optional[GrowthProposal]:
        result = await self._session.execute(
            select(ProposalRow).where(ProposalRow.id == proposal_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        row.status = status.value
        await self._session.commit()
        return self._row_to_proposal(row)

    # --- Evaluations ---

    async def save_evaluation(
        self, evaluation: EvaluationResult
    ) -> EvaluationResult:
        snap = evaluation.invariant_snapshot
        row = EvaluationRow(
            id=evaluation.id,
            proposal_id=evaluation.proposal_id,
            evaluated_at=evaluation.evaluated_at,
            decision=evaluation.decision.value,
            snapshot_delta_b=float(snap.delta_b),
            snapshot_delta_h=float(snap.delta_h),
            snapshot_r=float(snap.r),
            snapshot_s=float(snap.s),
            snapshot_u=float(snap.u),
            snapshot_index=float(snap.index),
            snapshot_growth_permitted=snap.growth_permitted,
            pipeline_stages=[
                s.model_dump(mode="json") for s in evaluation.pipeline_stages
            ],
            test_class_results=[
                t.model_dump(mode="json")
                for t in evaluation.test_class_results
            ],
            violations=[v.value for v in evaluation.violations],
            gate_conditions_met=evaluation.gate_conditions_met,
            firmware_allow_growth=evaluation.firmware_allow_growth,
            reasoning=evaluation.reasoning,
            total_duration_ms=evaluation.total_duration_ms,
        )
        self._session.add(row)
        await self._session.commit()
        return evaluation

    async def get_evaluation(
        self, evaluation_id: uuid.UUID
    ) -> Optional[EvaluationResult]:
        result = await self._session.execute(
            select(EvaluationRow).where(EvaluationRow.id == evaluation_id)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return self._row_to_evaluation(row)

    async def list_evaluations(
        self,
        proposal_id: Optional[uuid.UUID] = None,
        decision: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[EvaluationResult]:
        stmt = select(EvaluationRow).order_by(
            EvaluationRow.evaluated_at.desc()
        )
        if proposal_id:
            stmt = stmt.where(EvaluationRow.proposal_id == proposal_id)
        if decision:
            stmt = stmt.where(EvaluationRow.decision == decision)
        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [self._row_to_evaluation(r) for r in rows]

    # --- Audit Log ---

    async def log_audit(
        self,
        action: str,
        actor: str,
        proposal_id: Optional[uuid.UUID] = None,
        evaluation_id: Optional[uuid.UUID] = None,
        details: Optional[dict] = None,
        bodhisattva_index: Optional[Decimal] = None,
        growth_permitted: Optional[bool] = None,
    ) -> None:
        row = AuditLogRow(
            timestamp=datetime.now(timezone.utc),
            action=action,
            actor=actor,
            proposal_id=proposal_id,
            evaluation_id=evaluation_id,
            details=details or {},
            bodhisattva_index=(
                float(bodhisattva_index) if bodhisattva_index else None
            ),
            growth_permitted=growth_permitted,
        )
        self._session.add(row)
        await self._session.commit()

    async def get_audit_logs(
        self,
        action: Optional[str] = None,
        actor: Optional[str] = None,
        proposal_id: Optional[uuid.UUID] = None,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        stmt = select(AuditLogRow).order_by(AuditLogRow.timestamp.desc())
        if action:
            stmt = stmt.where(AuditLogRow.action == action)
        if actor:
            stmt = stmt.where(AuditLogRow.actor == actor)
        if proposal_id:
            stmt = stmt.where(AuditLogRow.proposal_id == proposal_id)
        if since:
            stmt = stmt.where(AuditLogRow.timestamp >= since)
        if until:
            stmt = stmt.where(AuditLogRow.timestamp <= until)
        stmt = stmt.limit(limit).offset(offset)

        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            {
                "id": str(r.id),
                "timestamp": r.timestamp.isoformat(),
                "action": r.action,
                "actor": r.actor,
                "proposal_id": str(r.proposal_id) if r.proposal_id else None,
                "evaluation_id": (
                    str(r.evaluation_id) if r.evaluation_id else None
                ),
                "details": r.details,
                "bodhisattva_index": (
                    str(r.bodhisattva_index)
                    if r.bodhisattva_index is not None
                    else None
                ),
                "growth_permitted": r.growth_permitted,
            }
            for r in rows
        ]

    # --- Compliance Reports ---

    async def save_compliance_report(
        self, report: ComplianceReport
    ) -> ComplianceReport:
        row = ComplianceReportRow(
            id=report.id,
            proposal_id=report.proposal_id,
            evaluation_id=report.evaluation_id,
            generated_at=report.generated_at,
            is_compliant=report.is_compliant,
            violations=[
                v.model_dump(mode="json") for v in report.violations
            ],
            institutional_diagnoses=[
                d.model_dump(mode="json")
                for d in report.institutional_diagnoses
            ],
            bodhisattva_index=float(report.bodhisattva_index),
            summary=report.summary,
        )
        self._session.add(row)
        await self._session.commit()
        return report

    # --- Converters ---

    def _row_to_proposal(self, row: ProposalRow) -> GrowthProposal:
        return GrowthProposal(
            id=row.id,
            title=row.title,
            description=row.description,
            domain=ProposalDomain(row.domain),
            submitted_by=row.submitted_by,
            submitted_at=row.submitted_at,
            status=ProposalStatus(row.status),
            delta_b=Decimal(str(row.delta_b)),
            delta_h=Decimal(str(row.delta_h)),
            r=Decimal(str(row.r)),
            s=Decimal(str(row.s)),
            u=Decimal(str(row.u)),
            human_signoff_required=row.human_signoff_required,
            human_signoff_obtained=row.human_signoff_obtained,
            rollback_plan=row.rollback_plan,
            uncertainty_explanation=row.uncertainty_explanation,
            stakeholder_impacts=row.stakeholder_impacts,
            tags=row.tags,
        )

    def _row_to_evaluation(self, row: EvaluationRow) -> EvaluationResult:
        from bodhisattva.core.types import EvaluationDecision, ViolationType

        snap = InvariantSnapshot(
            delta_b=Decimal(str(row.snapshot_delta_b)),
            delta_h=Decimal(str(row.snapshot_delta_h)),
            r=Decimal(str(row.snapshot_r)),
            s=Decimal(str(row.snapshot_s)),
            u=Decimal(str(row.snapshot_u)),
            index=Decimal(str(row.snapshot_index)),
            growth_permitted=row.snapshot_growth_permitted,
            benefit_harm_ratio=(
                Decimal(str(row.snapshot_delta_b))
                / Decimal(str(row.snapshot_delta_h))
            ),
            uncertainty_discount=(
                Decimal("1") - Decimal(str(row.snapshot_u))
            ),
        )

        return EvaluationResult(
            id=row.id,
            proposal_id=row.proposal_id,
            evaluated_at=row.evaluated_at,
            decision=EvaluationDecision(row.decision),
            invariant_snapshot=snap,
            pipeline_stages=[
                PipelineStageResult(**s) for s in (row.pipeline_stages or [])
            ],
            test_class_results=[
                TestClassResult(**t) for t in (row.test_class_results or [])
            ],
            violations=[
                ViolationType(v) for v in (row.violations or [])
            ],
            gate_conditions_met=row.gate_conditions_met,
            firmware_allow_growth=row.firmware_allow_growth,
            reasoning=row.reasoning,
            total_duration_ms=float(row.total_duration_ms),
        )
