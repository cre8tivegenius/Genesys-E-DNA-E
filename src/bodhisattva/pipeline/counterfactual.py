"""
Counterfactual Analysis.

Third stage of the BVP. Asks: what would happen if we DON'T proceed?
Compares the proposal's invariant against the status quo.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index


class CounterfactualAnalyzer:
    """Analyzes the counterfactual: what happens without the proposed growth?"""

    def analyze(self, proposal: object, inputs: InvariantInputs) -> dict:
        """
        Compare the proposal against a no-action baseline.

        The counterfactual assumes:
        - Benefit drops to 0 (no growth = no new benefit)
        - Harm remains (existing harm persists)
        - But also: harm may increase without intervention (stagnation risk)
        """
        proposal_result = compute_index(inputs)

        # Counterfactual: no action (benefit = minimal, harm persists)
        # We model this as benefit dropping to a fraction of current
        no_action_benefit = inputs.delta_b * Decimal("0.1")
        if no_action_benefit <= 0:
            no_action_benefit = Decimal("0.001")

        no_action = InvariantInputs(
            delta_b=no_action_benefit,
            delta_h=inputs.delta_h,
            r=Decimal("1"),  # No action = fully reversible (nothing changes)
            s=Decimal("1"),  # No scaling risk
            u=inputs.u * Decimal("0.5"),  # Less uncertainty in status quo
        )
        no_action_result = compute_index(no_action)

        # The proposal is counterfactually justified if it's better than inaction
        net_value = proposal_result.index - no_action_result.index
        passed = net_value > Decimal("0") and proposal_result.growth_permitted

        return {
            "passed": passed,
            "proposal_index": str(proposal_result.index),
            "no_action_index": str(no_action_result.index),
            "net_counterfactual_value": str(net_value),
            "proposal_growth_permitted": proposal_result.growth_permitted,
        }
