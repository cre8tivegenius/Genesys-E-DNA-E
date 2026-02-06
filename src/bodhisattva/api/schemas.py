"""API-specific request/response schemas."""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class QuickCheckRequest(BaseModel):
    delta_b: Decimal = Field(gt=0, description="Marginal benefit")
    delta_h: Decimal = Field(gt=0, description="Marginal harm")
    r: Decimal = Field(ge=0, le=1, description="Reversibility [0,1]")
    s: Decimal = Field(gt=0, description="Scale sensitivity")
    u: Decimal = Field(ge=0, le=1, description="Uncertainty [0,1]")


class EvaluateRequest(BaseModel):
    proposal_id: uuid.UUID


class ComplianceCheckRequest(BaseModel):
    proposal_id: uuid.UUID
    evaluation_id: uuid.UUID


class AdversarialTestRequest(BaseModel):
    baseline: dict[str, str] = Field(
        description="Baseline inputs: delta_b, delta_h, r, s, u"
    )


class StatusUpdateRequest(BaseModel):
    status: str


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
