"""
The ALLOW_GROWTH one-bit gate.

Implements the firmware-level constraint from spec Section I.A:

    bool ALLOW_GROWTH =
        (delta_B > delta_H) &&
        (R > 1/S) &&
        (U < U_MAX);

Combined with the composite Bodhisattva Index check (I > 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.types import DEFAULT_U_MAX


@dataclass(frozen=True, slots=True)
class GateConditions:
    """Individual conditions that compose the gate decision."""
    benefit_exceeds_harm: bool
    reversibility_sufficient: bool
    uncertainty_acceptable: bool
    index_above_threshold: bool


@dataclass(frozen=True, slots=True)
class GateDecision:
    """The complete gate decision with full audit trail."""
    allow_growth: bool
    conditions: GateConditions
    index_value: Decimal
    u_max: Decimal


def evaluate_gate(
    inputs: InvariantInputs,
    u_max: Decimal = DEFAULT_U_MAX,
) -> GateDecision:
    """
    Evaluate the one-bit ALLOW_GROWTH gate.

    Both the firmware boolean conditions AND the composite index must pass.

    Conditions:
        1. delta_B > delta_H
        2. R > 1/S
        3. U < U_MAX
        4. I > 1
    """
    result = compute_index(inputs)

    conditions = GateConditions(
        benefit_exceeds_harm=inputs.delta_b > inputs.delta_h,
        reversibility_sufficient=inputs.r > (Decimal("1") / inputs.s),
        uncertainty_acceptable=inputs.u < u_max,
        index_above_threshold=result.growth_permitted,
    )

    allow = all([
        conditions.benefit_exceeds_harm,
        conditions.reversibility_sufficient,
        conditions.uncertainty_acceptable,
        conditions.index_above_threshold,
    ])

    return GateDecision(
        allow_growth=allow,
        conditions=conditions,
        index_value=result.index,
        u_max=u_max,
    )
