"""Proposal endpoints."""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from bodhisattva.api.dependencies import get_repository
from bodhisattva.core.types import ProposalStatus
from bodhisattva.db.repository import Repository
from bodhisattva.models.proposal import GrowthProposal
from bodhisattva.api.schemas import StatusUpdateRequest

router = APIRouter()


@router.post("/proposals", response_model=GrowthProposal, status_code=201)
async def create_proposal(
    proposal: GrowthProposal,
    repo: Repository = Depends(get_repository),
) -> GrowthProposal:
    """Create a new growth proposal."""
    result = await repo.save_proposal(proposal)
    await repo.log_audit(
        action="proposal_submitted",
        actor=proposal.submitted_by,
        proposal_id=result.id,
    )
    return result


@router.get("/proposals/{proposal_id}", response_model=GrowthProposal)
async def get_proposal(
    proposal_id: uuid.UUID,
    repo: Repository = Depends(get_repository),
) -> GrowthProposal:
    """Get a proposal by ID."""
    proposal = await repo.get_proposal(proposal_id)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal


@router.get("/proposals", response_model=list[GrowthProposal])
async def list_proposals(
    status: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    repo: Repository = Depends(get_repository),
) -> list[GrowthProposal]:
    """List proposals with optional filters."""
    return await repo.list_proposals(
        status=status,
        domain=domain,
        limit=size,
        offset=(page - 1) * size,
    )


@router.patch(
    "/proposals/{proposal_id}", response_model=GrowthProposal
)
async def update_proposal_status(
    proposal_id: uuid.UUID,
    body: StatusUpdateRequest,
    repo: Repository = Depends(get_repository),
) -> GrowthProposal:
    """Update a proposal's status."""
    try:
        new_status = ProposalStatus(body.status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status: {body.status}",
        )

    result = await repo.update_proposal_status(proposal_id, new_status)
    if not result:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return result
