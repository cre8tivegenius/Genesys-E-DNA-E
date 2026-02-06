"""Evaluation endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from bodhisattva.api.dependencies import get_pipeline, get_repository
from bodhisattva.api.schemas import EvaluateRequest, QuickCheckRequest
from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.db.repository import Repository
from bodhisattva.models.evaluation import EvaluationResult, InvariantSnapshot
from bodhisattva.pipeline.bvp import BodhisattvaValidationPipeline

router = APIRouter()


@router.post("/evaluations", response_model=EvaluationResult, status_code=201)
async def create_evaluation(
    request: EvaluateRequest,
    pipeline: BodhisattvaValidationPipeline = Depends(get_pipeline),
    repo: Repository = Depends(get_repository),
) -> EvaluationResult:
    """Submit a proposal for full BVP evaluation."""
    proposal = await repo.get_proposal(request.proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    result = await pipeline.evaluate(proposal)
    await repo.save_evaluation(result)
    await repo.log_audit(
        action="evaluation_completed",
        actor="system",
        proposal_id=proposal.id,
        evaluation_id=result.id,
        bodhisattva_index=result.invariant_snapshot.index,
        growth_permitted=result.invariant_snapshot.growth_permitted,
    )
    return result


@router.post("/evaluations/quick", response_model=InvariantSnapshot)
async def quick_check(request: QuickCheckRequest) -> InvariantSnapshot:
    """Quick invariant computation without persistence."""
    inputs = InvariantInputs(
        delta_b=request.delta_b,
        delta_h=request.delta_h,
        r=request.r,
        s=request.s,
        u=request.u,
    )
    result = compute_index(inputs)
    return InvariantSnapshot(
        delta_b=inputs.delta_b,
        delta_h=inputs.delta_h,
        r=inputs.r,
        s=inputs.s,
        u=inputs.u,
        index=result.index,
        growth_permitted=result.growth_permitted,
        benefit_harm_ratio=result.benefit_harm_ratio,
        uncertainty_discount=result.uncertainty_discount,
    )


@router.get(
    "/evaluations/{evaluation_id}", response_model=EvaluationResult
)
async def get_evaluation(
    evaluation_id: uuid.UUID,
    repo: Repository = Depends(get_repository),
) -> EvaluationResult:
    """Get an evaluation by ID."""
    result = await repo.get_evaluation(evaluation_id)
    if not result:
        raise HTTPException(
            status_code=404, detail="Evaluation not found"
        )
    return result


@router.get("/evaluations", response_model=list[EvaluationResult])
async def list_evaluations(
    proposal_id: Optional[uuid.UUID] = Query(None),
    decision: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    repo: Repository = Depends(get_repository),
) -> list[EvaluationResult]:
    """List evaluations with optional filters."""
    return await repo.list_evaluations(
        proposal_id=proposal_id,
        decision=decision,
        limit=size,
        offset=(page - 1) * size,
    )
