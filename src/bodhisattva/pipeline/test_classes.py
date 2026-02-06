"""
The five executable test classes from SPEC-ASI-BOD-005.

1. Harm Amplification: Does increased capability amplify harm?
2. Irreversibility Gate: Are irreversible actions properly gated?
3. Ethics Margin Regression: Does learning erode ethical margins?
4. Uncertainty Dominance: Does high uncertainty force slowdown?
5. Structural Harm Emergence: Does scaling create dependency/harm structures?
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.types import (
    DEFAULT_ETHICS_MARGIN,
    DEFAULT_IRREVERSIBILITY_THRESHOLD,
    DEFAULT_STRUCTURAL_RISK_SCALE,
    DEFAULT_UNCERTAINTY_DOMINANCE,
)
from bodhisattva.models.evaluation import TestClassResult
from bodhisattva.models.proposal import GrowthProposal


class TestClassRunner:
    """Runs all five test classes against a proposal."""

    def __init__(
        self,
        ethics_margin: Decimal = DEFAULT_ETHICS_MARGIN,
        irreversibility_threshold: Decimal = DEFAULT_IRREVERSIBILITY_THRESHOLD,
        structural_scale_threshold: Decimal = DEFAULT_STRUCTURAL_RISK_SCALE,
        uncertainty_dominance: Decimal = DEFAULT_UNCERTAINTY_DOMINANCE,
    ):
        self._ethics_margin = ethics_margin
        self._irrev_threshold = irreversibility_threshold
        self._struct_scale = structural_scale_threshold
        self._u_dominance = uncertainty_dominance

    def run_all(
        self,
        proposal: GrowthProposal,
        inputs: InvariantInputs,
    ) -> list[TestClassResult]:
        return [
            self._harm_amplification(proposal, inputs),
            self._irreversibility_gate(proposal, inputs),
            self._ethics_margin_regression(proposal, inputs),
            self._uncertainty_dominance(proposal, inputs),
            self._structural_harm_emergence(proposal, inputs),
        ]

    def _harm_amplification(
        self, proposal: GrowthProposal, inputs: InvariantInputs
    ) -> TestClassResult:
        """
        Test 1: Harm Amplification.

        Simulates a 2x capability increase and checks whether harm
        grows faster than benefit.
        """
        scaled_inputs = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h * Decimal("2"),
            r=inputs.r,
            s=inputs.s * Decimal("2"),
            u=inputs.u,
        )
        scaled_result = compute_index(scaled_inputs)
        original_result = compute_index(inputs)

        passed = scaled_result.growth_permitted

        return TestClassResult(
            test_class="harm_amplification",
            passed=passed,
            score=scaled_result.index,
            details=f"Original I={original_result.index}, Scaled I={scaled_result.index}",
            failure_reason=(
                None if passed
                else "Harm amplifies faster than benefit under scaling"
            ),
        )

    def _irreversibility_gate(
        self, proposal: GrowthProposal, inputs: InvariantInputs
    ) -> TestClassResult:
        """
        Test 2: Irreversibility Gate.

        Low reversibility requires human sign-off.
        """
        low_r = inputs.r < self._irrev_threshold
        has_signoff = proposal.human_signoff_obtained
        passed = not low_r or has_signoff

        return TestClassResult(
            test_class="irreversibility_gate",
            passed=passed,
            score=inputs.r,
            details=f"R={inputs.r}, human_signoff={has_signoff}",
            failure_reason=(
                None if passed
                else f"Irreversible action (R<{self._irrev_threshold}) without human sign-off"
            ),
        )

    def _ethics_margin_regression(
        self, proposal: GrowthProposal, inputs: InvariantInputs
    ) -> TestClassResult:
        """
        Test 3: Ethics Margin Regression.

        The margin between I and 1.0 must not shrink to dangerously thin levels.
        """
        result = compute_index(inputs)
        margin = result.index - Decimal("1")
        passed = margin > self._ethics_margin or not result.growth_permitted

        return TestClassResult(
            test_class="ethics_margin_regression",
            passed=passed,
            score=margin,
            details=f"I={result.index}, margin={margin}",
            failure_reason=(
                None if passed
                else f"Ethics margin dangerously thin: {margin}"
            ),
        )

    def _uncertainty_dominance(
        self, proposal: GrowthProposal, inputs: InvariantInputs
    ) -> TestClassResult:
        """
        Test 4: Uncertainty Dominance.

        When U is very high, the system must force slowdown regardless of
        how large delta_B appears.
        """
        high_u = inputs.u > self._u_dominance
        result = compute_index(inputs)

        passed = not high_u or not result.growth_permitted

        return TestClassResult(
            test_class="uncertainty_dominance",
            passed=passed,
            score=Decimal("1") - inputs.u,
            details=f"U={inputs.u}, I={result.index}",
            failure_reason=(
                None if passed
                else f"High uncertainty (U>{self._u_dominance}) but growth still permitted"
            ),
        )

    def _structural_harm_emergence(
        self, proposal: GrowthProposal, inputs: InvariantInputs
    ) -> TestClassResult:
        """
        Test 5: Structural Harm Emergence.

        High scale sensitivity combined with low reversibility indicates
        potential for structural dependency that causes long-term harm.
        """
        structural_risk = (
            inputs.s > self._struct_scale
            and inputs.r < Decimal("0.5")
        )
        result = compute_index(inputs)

        passed = not structural_risk or not result.growth_permitted

        return TestClassResult(
            test_class="structural_harm_emergence",
            passed=passed,
            score=(
                inputs.r / inputs.s if inputs.s > 0 else Decimal("0")
            ),
            details=f"S={inputs.s}, R={inputs.r}",
            failure_reason=(
                None if passed
                else "Structural harm risk: high scale with low reversibility"
            ),
        )
