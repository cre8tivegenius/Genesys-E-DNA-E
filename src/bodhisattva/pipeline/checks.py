"""
Invariant Check Runners.

Fourth stage of the BVP. Runs the core invariant computation
and all gate conditions, producing a detailed check report.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.gate import evaluate_gate
from bodhisattva.core.types import DEFAULT_U_MAX


class InvariantChecker:
    """Runs all invariant checks and gate conditions."""

    def __init__(self, u_max: Decimal = DEFAULT_U_MAX):
        self._u_max = u_max

    def check(self, inputs: InvariantInputs) -> dict:
        """
        Run the full invariant check suite.

        Checks:
        1. Core index computation (I > 1)
        2. Benefit exceeds harm (delta_B > delta_H)
        3. Reversibility sufficient (R > 1/S)
        4. Uncertainty acceptable (U < U_MAX)
        """
        result = compute_index(inputs)
        gate = evaluate_gate(inputs, self._u_max)

        checks = {
            "index_above_threshold": {
                "passed": gate.conditions.index_above_threshold,
                "value": str(result.index),
                "threshold": "1",
            },
            "benefit_exceeds_harm": {
                "passed": gate.conditions.benefit_exceeds_harm,
                "delta_b": str(inputs.delta_b),
                "delta_h": str(inputs.delta_h),
            },
            "reversibility_sufficient": {
                "passed": gate.conditions.reversibility_sufficient,
                "r": str(inputs.r),
                "threshold": str(Decimal("1") / inputs.s),
            },
            "uncertainty_acceptable": {
                "passed": gate.conditions.uncertainty_acceptable,
                "u": str(inputs.u),
                "u_max": str(self._u_max),
            },
        }

        all_passed = all(c["passed"] for c in checks.values())

        return {
            "passed": all_passed,
            "gate_allow_growth": gate.allow_growth,
            "index": str(result.index),
            "checks": checks,
        }
