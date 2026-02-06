"""Pydantic models for evaluation results."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from bodhisattva.core.types import EvaluationDecision, ViolationType


class TestClassResult(BaseModel):
    """Result from one of the five BVP test classes."""
    test_class: str
    passed: bool
    score: Decimal
    details: str
    failure_reason: Optional[str] = None


class InvariantSnapshot(BaseModel):
    """A frozen snapshot of invariant computation for audit."""
    delta_b: Decimal
    delta_h: Decimal
    r: Decimal
    s: Decimal
    u: Decimal
    index: Decimal
    growth_permitted: bool
    benefit_harm_ratio: Decimal
    uncertainty_discount: Decimal


class PipelineStageResult(BaseModel):
    """Result from a single BVP pipeline stage."""
    stage_name: str
    passed: bool
    duration_ms: float
    details: dict = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class EvaluationResult(BaseModel):
    """Complete result of evaluating a proposal through the BVP."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    proposal_id: uuid.UUID
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Core decision
    decision: EvaluationDecision
    invariant_snapshot: InvariantSnapshot

    # Pipeline details
    pipeline_stages: list[PipelineStageResult] = Field(default_factory=list)
    test_class_results: list[TestClassResult] = Field(default_factory=list)
    violations: list[ViolationType] = Field(default_factory=list)

    # Gate conditions (firmware-level)
    gate_conditions_met: bool
    firmware_allow_growth: bool

    # Audit
    reasoning: str
    total_duration_ms: float
