"""Pydantic models for firmware gate simulation."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

from bodhisattva.core.types import AutonomyLevel


class GrowthProof(BaseModel):
    """A cryptographic proof that the Bodhisattva Index > 1."""
    proof_id: str
    timestamp: str
    inputs_hash: str
    index_value: str
    gate_allowed: bool
    signature: str
    nonce: str


class FirmwareState(BaseModel):
    """The simulated state of the firmware gate."""
    allow_growth: bool
    clock_rate_capped: bool
    autonomy_level: AutonomyLevel
    learning_writes_enabled: bool
    external_actuation_enabled: bool
    index_value: Decimal
    growth_proof: Optional[GrowthProof] = None
