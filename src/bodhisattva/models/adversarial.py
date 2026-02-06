"""Pydantic models for adversarial resilience testing."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel

from bodhisattva.core.types import AttackVector


class AdversarialScenario(BaseModel):
    """Definition of an adversarial test scenario."""
    name: str
    attack_vector: AttackVector
    description: str
    baseline_inputs: dict[str, str]
    adversarial_inputs: dict[str, str]
    true_inputs: dict[str, str]


class ResilienceResult(BaseModel):
    """Result of adversarial resilience testing."""
    scenario_name: str
    attack_vector: AttackVector
    invariant_survived: bool
    adversarial_index: Decimal
    adversarial_growth_permitted: bool
    true_index: Decimal
    true_growth_permitted: bool
    coupling_blocked: bool
    explanation: str
