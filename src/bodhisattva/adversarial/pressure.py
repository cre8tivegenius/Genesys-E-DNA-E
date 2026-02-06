"""
Optimization pressure simulation.

Simulates an optimizer trying to maximize growth permission
by manipulating individual variables, demonstrating that the
multiplicative coupling of the invariant resists single-axis exploits.
"""

from __future__ import annotations

from decimal import Decimal
from dataclasses import dataclass

from bodhisattva.core.invariant import InvariantInputs, compute_index


@dataclass(frozen=True, slots=True)
class PressureResult:
    """Result of applying optimization pressure to a single variable."""
    variable: str
    original_value: Decimal
    optimized_value: Decimal
    original_index: Decimal
    optimized_index: Decimal
    growth_flipped: bool  # Did the optimization flip the gate?
    max_achievable_index: Decimal


def apply_single_axis_pressure(
    inputs: InvariantInputs,
    variable: str,
    pressure_factor: Decimal = Decimal("10"),
) -> PressureResult:
    """
    Apply maximum optimization pressure to a single variable.

    Demonstrates that changing one variable alone cannot reliably
    flip the gate when other variables remain truthful.
    """
    original = compute_index(inputs)
    original_val = getattr(inputs, variable)

    # Apply pressure in the direction that would increase I
    kwargs = {
        "delta_b": inputs.delta_b,
        "delta_h": inputs.delta_h,
        "r": inputs.r,
        "s": inputs.s,
        "u": inputs.u,
    }

    if variable == "delta_b":
        # Inflate benefit
        optimized_val = original_val * pressure_factor
        kwargs["delta_b"] = optimized_val
    elif variable == "delta_h":
        # Minimize reported harm
        optimized_val = max(
            original_val / pressure_factor, Decimal("0.001")
        )
        kwargs["delta_h"] = optimized_val
    elif variable == "r":
        # Maximize reversibility
        optimized_val = Decimal("1")
        kwargs["r"] = optimized_val
    elif variable == "s":
        # Minimize scale sensitivity
        optimized_val = max(
            original_val / pressure_factor, Decimal("0.001")
        )
        kwargs["s"] = optimized_val
    elif variable == "u":
        # Minimize uncertainty
        optimized_val = Decimal("0")
        kwargs["u"] = optimized_val
    else:
        raise ValueError(f"Unknown variable: {variable}")

    optimized_inputs = InvariantInputs(**kwargs)
    optimized = compute_index(optimized_inputs)

    return PressureResult(
        variable=variable,
        original_value=original_val,
        optimized_value=optimized_val,
        original_index=original.index,
        optimized_index=optimized.index,
        growth_flipped=(
            not original.growth_permitted and optimized.growth_permitted
        ),
        max_achievable_index=optimized.index,
    )


def full_pressure_analysis(
    inputs: InvariantInputs,
    pressure_factor: Decimal = Decimal("10"),
) -> list[PressureResult]:
    """
    Apply pressure to each variable independently and report results.

    This demonstrates the spec's claim: "There is no single axis to exploit."
    """
    variables = ["delta_b", "delta_h", "r", "s", "u"]
    return [
        apply_single_axis_pressure(inputs, var, pressure_factor)
        for var in variables
    ]
