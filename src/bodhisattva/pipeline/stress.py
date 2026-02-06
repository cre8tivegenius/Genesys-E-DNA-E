"""
Stress Simulation.

Second stage of the BVP. Simulates the proposal under adverse conditions
by perturbing inputs and checking if the invariant holds.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index


class StressSimulator:
    """Stress-tests the invariant under perturbed conditions."""

    def __init__(
        self,
        harm_multiplier: Decimal = Decimal("2"),
        scale_multiplier: Decimal = Decimal("3"),
        uncertainty_bump: Decimal = Decimal("0.2"),
        reversibility_reduction: Decimal = Decimal("0.3"),
    ):
        self._harm_mult = harm_multiplier
        self._scale_mult = scale_multiplier
        self._u_bump = uncertainty_bump
        self._r_reduction = reversibility_reduction

    def simulate(self, proposal: object, inputs: InvariantInputs) -> dict:
        """
        Run stress scenarios and return results.

        Scenarios:
        1. Harm doubles
        2. Scale triples
        3. Uncertainty increases by 0.2
        4. Reversibility drops by 0.3
        5. All adverse conditions combined
        """
        baseline = compute_index(inputs)
        scenarios: list[dict] = []

        # Scenario 1: Harm amplification
        stressed_h = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h * self._harm_mult,
            r=inputs.r,
            s=inputs.s,
            u=inputs.u,
        )
        r1 = compute_index(stressed_h)
        scenarios.append({
            "name": "harm_amplification",
            "index": str(r1.index),
            "growth_permitted": r1.growth_permitted,
        })

        # Scenario 2: Scale increase
        stressed_s = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h,
            r=inputs.r,
            s=inputs.s * self._scale_mult,
            u=inputs.u,
        )
        r2 = compute_index(stressed_s)
        scenarios.append({
            "name": "scale_increase",
            "index": str(r2.index),
            "growth_permitted": r2.growth_permitted,
        })

        # Scenario 3: Uncertainty increase
        new_u = min(inputs.u + self._u_bump, Decimal("1"))
        stressed_u = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h,
            r=inputs.r,
            s=inputs.s,
            u=new_u,
        )
        r3 = compute_index(stressed_u)
        scenarios.append({
            "name": "uncertainty_increase",
            "index": str(r3.index),
            "growth_permitted": r3.growth_permitted,
        })

        # Scenario 4: Reversibility reduction
        new_r = max(inputs.r - self._r_reduction, Decimal("0"))
        stressed_r = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h,
            r=new_r,
            s=inputs.s,
            u=inputs.u,
        )
        r4 = compute_index(stressed_r)
        scenarios.append({
            "name": "reversibility_reduction",
            "index": str(r4.index),
            "growth_permitted": r4.growth_permitted,
        })

        # Scenario 5: Combined worst case
        combined = InvariantInputs(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h * self._harm_mult,
            r=new_r,
            s=inputs.s * self._scale_mult,
            u=new_u,
        )
        r5 = compute_index(combined)
        scenarios.append({
            "name": "combined_worst_case",
            "index": str(r5.index),
            "growth_permitted": r5.growth_permitted,
        })

        # Passes if baseline holds and at least some stress scenarios pass
        surviving = sum(1 for s in scenarios if s["growth_permitted"])
        passed = baseline.growth_permitted and surviving >= 2

        return {
            "passed": passed,
            "baseline_index": str(baseline.index),
            "scenarios": scenarios,
            "scenarios_surviving": surviving,
            "total_scenarios": len(scenarios),
        }
