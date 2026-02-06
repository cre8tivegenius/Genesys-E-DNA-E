"""Compliance endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from bodhisattva.api.dependencies import (
    get_compliance_checker,
    get_repository,
)
from bodhisattva.api.schemas import ComplianceCheckRequest
from bodhisattva.db.repository import Repository
from bodhisattva.models.compliance import ComplianceReport
from bodhisattva.regulatory.compliance import ComplianceChecker

router = APIRouter()


@router.post(
    "/compliance/check",
    response_model=ComplianceReport,
    status_code=201,
)
async def check_compliance(
    request: ComplianceCheckRequest,
    checker: ComplianceChecker = Depends(get_compliance_checker),
    repo: Repository = Depends(get_repository),
) -> ComplianceReport:
    """Run a compliance check against a proposal and evaluation."""
    proposal = await repo.get_proposal(request.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    evaluation = await repo.get_evaluation(request.evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=404, detail="Evaluation not found"
        )

    report = checker.check_proposal(proposal, evaluation)
    await repo.save_compliance_report(report)
    await repo.log_audit(
        action="compliance_check",
        actor="system",
        proposal_id=proposal.id,
        evaluation_id=evaluation.id,
        details={"is_compliant": report.is_compliant},
        bodhisattva_index=report.bodhisattva_index,
    )
    return report
