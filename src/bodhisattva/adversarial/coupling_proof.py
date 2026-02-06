"""
Multiplicative coupling proof.

Formally demonstrates that the Bodhisattva invariant's multiplicative
structure prevents any single-axis exploit from flipping the gate.

Per spec Section III.B:
"Because the invariant is multiplicative and coupled:
 - Inflating delta_B without reducing delta_H -> blocked
 - Hiding uncertainty increases U -> blocked
 - Scaling increases S -> blocked
 - Irreversibility collapses R -> blocked

There is no single axis to exploit.
Any attempt to cheat one term worsens another.
This makes the system anti-fragile under adversarial pressure."
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.adversarial.pressure import full_pressure_analysis, PressureResult


@dataclass(frozen=True, slots=True)
class CouplingProofResult:
    """Result of the coupling proof analysis."""
    inputs_deny_growth: bool
    single_axis_results: list[PressureResult]
    any_single_axis_flips: bool
    variables_that_flip: list[str]
    proof_holds: bool  # True if no single-axis flip occurred
    explanation: str


def prove_coupling(
    inputs: InvariantInputs,
    pressure_factor: Decimal = Decimal("10"),
) -> CouplingProofResult:
    """
    Prove that the multiplicative coupling prevents single-axis exploits.

    Given inputs that deny growth (I <= 1), show that optimizing
    any single variable by the pressure factor cannot flip the gate.

    For inputs that already allow growth, the proof is trivially satisfied
    (the attacker has no reason to exploit).
    """
    result = compute_index(inputs)

    if result.growth_permitted:
        return CouplingProofResult(
            inputs_deny_growth=False,
            single_axis_results=[],
            any_single_axis_flips=False,
            variables_that_flip=[],
            proof_holds=True,
            explanation=(
                "Growth already permitted (I > 1). "
                "No adversarial incentive to manipulate."
            ),
        )

    results = full_pressure_analysis(inputs, pressure_factor)
    flipped = [r for r in results if r.growth_flipped]

    proof_holds = len(flipped) == 0

    if proof_holds:
        explanation = (
            f"With pressure factor {pressure_factor}x, no single variable "
            f"manipulation can flip the gate from DENY to ALLOW. "
            f"The multiplicative coupling holds."
        )
    else:
        vars_that_flip = [r.variable for r in flipped]
        explanation = (
            f"WARNING: Variable(s) {vars_that_flip} can flip the gate "
            f"with {pressure_factor}x pressure. This indicates the "
            f"inputs are close to the I=1 boundary and the coupling "
            f"is weak for this configuration."
        )

    return CouplingProofResult(
        inputs_deny_growth=True,
        single_axis_results=results,
        any_single_axis_flips=not proof_holds,
        variables_that_flip=[r.variable for r in flipped],
        proof_holds=proof_holds,
        explanation=explanation,
    )
