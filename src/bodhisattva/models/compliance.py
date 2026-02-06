"""Pydantic models for regulatory compliance."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from bodhisattva.core.types import InstitutionalFailureType, ViolationType


class ComplianceViolation(BaseModel):
    """A single compliance violation with full context."""
    violation_type: ViolationType
    severity: str  # "critical", "major", "minor"
    dna_term_violated: str
    description: str
    remediation: str


class InstitutionalDiagnosis(BaseModel):
    """Maps a pattern to a known institutional failure mode."""
    failure_type: InstitutionalFailureType
    dna_term: str
    confidence: Decimal
    description: str


class ComplianceReport(BaseModel):
    """Full compliance report for a proposal or evaluation."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    proposal_id: uuid.UUID
    evaluation_id: Optional[uuid.UUID] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    is_compliant: bool
    violations: list[ComplianceViolation] = Field(default_factory=list)
    institutional_diagnoses: list[InstitutionalDiagnosis] = Field(default_factory=list)
    bodhisattva_index: Decimal
    summary: str
