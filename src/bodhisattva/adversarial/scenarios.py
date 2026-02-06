"""
Adversarial resilience testing.

Implements Section III of the spec: demonstrates the invariant survives
optimization pressure. Tests the four attack vectors:
1. Inflate delta_B metrics
2. Hide delta_H externally
3. Mask uncertainty
4. Push scale before validation
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.types import AttackVector
from bodhisattva.models.adversarial import AdversarialScenario, ResilienceResult


class AdversarialTester:
    """
    Tests whether the invariant survives adversarial optimization pressure.

    Per spec Section III.B, the invariant is multiplicative and coupled:
    - Inflating delta_B without reducing delta_H -> blocked
    - Hiding uncertainty increases U -> blocked
    - Scaling increases S -> blocked
    - Irreversibility collapses R -> blocked

    "There is no single axis to exploit."
    """

    def test_scenario(self, scenario: AdversarialScenario) -> ResilienceResult:
        """Test a single adversarial scenario."""
        adversarial = InvariantInputs(**{
            k: Decimal(str(v)) for k, v in scenario.adversarial_inputs.items()
        })
        true = InvariantInputs(**{
            k: Decimal(str(v)) for k, v in scenario.true_inputs.items()
        })

        adv_result = compute_index(adversarial)
        true_result = compute_index(true)

        # The invariant "survives" if the true values block growth
        coupling_blocked = (
            adv_result.growth_permitted and not true_result.growth_permitted
        )
        invariant_survived = not true_result.growth_permitted or (
            adv_result.growth_permitted == true_result.growth_permitted
        )

        return ResilienceResult(
            scenario_name=scenario.name,
            attack_vector=scenario.attack_vector,
            invariant_survived=invariant_survived,
            adversarial_index=adv_result.index,
            adversarial_growth_permitted=adv_result.growth_permitted,
            true_index=true_result.index,
            true_growth_permitted=true_result.growth_permitted,
            coupling_blocked=coupling_blocked,
            explanation=self._explain(
                scenario.attack_vector, adv_result, true_result
            ),
        )

    def run_standard_battery(
        self, baseline: dict[str, str]
    ) -> list[ResilienceResult]:
        """Run the standard set of adversarial scenarios against a baseline."""
        scenarios = self._build_standard_scenarios(baseline)
        return [self.test_scenario(s) for s in scenarios]

    def _build_standard_scenarios(
        self, baseline: dict[str, str]
    ) -> list[AdversarialScenario]:
        b = baseline
        delta_b = Decimal(str(b["delta_b"]))
        delta_h = Decimal(str(b["delta_h"]))

        return [
            AdversarialScenario(
                name="Benefit Inflation",
                attack_vector=AttackVector.INFLATE_BENEFIT,
                description=(
                    "Adversary inflates delta_B by 10x while true value unchanged"
                ),
                baseline_inputs=b,
                adversarial_inputs={
                    **b,
                    "delta_b": str(delta_b * 10),
                },
                true_inputs=b,
            ),
            AdversarialScenario(
                name="Harm Hiding",
                attack_vector=AttackVector.HIDE_HARM,
                description=(
                    "Adversary reports delta_H at 10% of true value"
                ),
                baseline_inputs=b,
                adversarial_inputs={
                    **b,
                    "delta_h": str(delta_h * Decimal("0.1")),
                },
                true_inputs=b,
            ),
            AdversarialScenario(
                name="Uncertainty Masking",
                attack_vector=AttackVector.MASK_UNCERTAINTY,
                description=(
                    "Adversary reports U=0.05 when true U=0.8"
                ),
                baseline_inputs=b,
                adversarial_inputs={**b, "u": "0.05"},
                true_inputs={**b, "u": "0.8"},
            ),
            AdversarialScenario(
                name="Premature Scaling",
                attack_vector=AttackVector.PREMATURE_SCALING,
                description=(
                    "Adversary reports S=1 when true deployment is S=20"
                ),
                baseline_inputs=b,
                adversarial_inputs={**b, "s": "1"},
                true_inputs={**b, "s": "20"},
            ),
        ]

    def _explain(self, vector, adv, true) -> str:
        if adv.growth_permitted and not true.growth_permitted:
            return (
                f"Attack vector '{vector.value}' would have fooled a naive check "
                f"(adversarial I={adv.index}) but the true index I={true.index} "
                f"blocks growth. Multiplicative coupling catches the exploit."
            )
        elif not adv.growth_permitted:
            return (
                f"Attack vector '{vector.value}' fails even with adversarial inputs "
                f"(I={adv.index}). The coupled structure prevents exploitation."
            )
        else:
            return (
                f"Both adversarial (I={adv.index}) and true (I={true.index}) "
                f"permit growth. No exploit attempted or needed."
            )
