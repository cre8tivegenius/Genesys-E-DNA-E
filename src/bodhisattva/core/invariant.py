"""
Core Bodhisattva Invariant Engine.

Pure computation. No side effects. No I/O.

Primary invariant:
    I = (delta_B * R) / (delta_H * S) * (1 - U)
    Growth is permitted iff I > 1.

Uses Decimal arithmetic for exact reproducibility at the I=1 boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


class InvariantError(Exception):
    """Raised when invariant inputs are physically impossible."""


@dataclass(frozen=True, slots=True)
class InvariantInputs:
    """Validated, immutable inputs to the Bodhisattva Index computation."""
    delta_b: Decimal  # Marginal benefit (>= 0)
    delta_h: Decimal  # Marginal harm (> 0)
    r: Decimal        # Reversibility [0, 1]
    s: Decimal        # Scale sensitivity (> 0)
    u: Decimal        # Uncertainty [0, 1]

    def __post_init__(self) -> None:
        if self.delta_b < 0:
            raise InvariantError("delta_b (marginal benefit) cannot be negative")
        if self.delta_h <= 0:
            raise InvariantError("delta_h (marginal harm) must be positive")
        if not (Decimal("0") <= self.r <= Decimal("1")):
            raise InvariantError("r (reversibility) must be in [0, 1]")
        if self.s <= 0:
            raise InvariantError("s (scale sensitivity) must be positive")
        if not (Decimal("0") <= self.u <= Decimal("1")):
            raise InvariantError("u (uncertainty) must be in [0, 1]")


@dataclass(frozen=True, slots=True)
class InvariantResult:
    """Result of computing the Bodhisattva Index."""
    index: Decimal
    growth_permitted: bool
    inputs: InvariantInputs
    benefit_harm_ratio: Decimal
    uncertainty_discount: Decimal


def compute_index(inputs: InvariantInputs) -> InvariantResult:
    """
    Compute the Bodhisattva Index.

    I = (delta_B * R) / (delta_H * S) * (1 - U)

    Growth is permitted iff I > 1 (strictly greater).
    """
    numerator = inputs.delta_b * inputs.r
    denominator = inputs.delta_h * inputs.s
    uncertainty_discount = Decimal("1") - inputs.u

    index = (numerator / denominator) * uncertainty_discount

    return InvariantResult(
        index=index,
        growth_permitted=index > Decimal("1"),
        inputs=inputs,
        benefit_harm_ratio=inputs.delta_b / inputs.delta_h,
        uncertainty_discount=uncertainty_discount,
    )
