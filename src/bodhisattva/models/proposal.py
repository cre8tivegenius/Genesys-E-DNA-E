"""Pydantic models for growth proposals."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from bodhisattva.core.types import ProposalDomain, ProposalStatus


class StakeholderImpact(BaseModel):
    """Who gains and who bears the downside (Section IV.A)."""
    stakeholder_id: str
    description: str
    benefit_estimate: Decimal = Field(ge=0)
    harm_estimate: Decimal = Field(ge=0)
    reversible: bool
    notes: Optional[str] = None


class GrowthProposal(BaseModel):
    """A proposal for capability growth, to be evaluated against the invariant."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)

    # Metadata
    title: str = Field(min_length=1, max_length=500)
    description: str
    domain: ProposalDomain
    submitted_by: str
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: ProposalStatus = ProposalStatus.DRAFT

    # Core invariant inputs
    delta_b: Decimal = Field(gt=0, description="Marginal benefit")
    delta_h: Decimal = Field(gt=0, description="Marginal harm")
    r: Decimal = Field(ge=0, le=1, description="Reversibility [0,1]")
    s: Decimal = Field(gt=0, description="Scale sensitivity")
    u: Decimal = Field(ge=0, le=1, description="Uncertainty [0,1]")

    # Context
    stakeholder_impacts: list[StakeholderImpact] = Field(default_factory=list)
    human_signoff_required: bool = False
    human_signoff_obtained: bool = False
    rollback_plan: Optional[str] = None
    uncertainty_explanation: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
