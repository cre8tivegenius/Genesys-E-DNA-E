"""
Non-compliance detection.

Implements the four non-compliance conditions from Section II.B:
1. Harm scales faster than benefit
2. Irreversible actions occur without human sign-off
3. Learning updates cannot be rolled back
4. The system cannot explain its uncertainty bounds
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.core.types import ViolationType
from bodhisattva.models.proposal import GrowthProposal


def detect_violations(
    proposal: GrowthProposal,
    inputs: InvariantInputs,
    irreversibility_threshold: Decimal = Decimal("0.5"),
) -> list[ViolationType]:
    """
    Detect all regulatory violations for a proposal.

    Returns a list of ViolationType enums for each violated condition.
    """
    violations: list[ViolationType] = []

    # 1. Harm scales faster than benefit
    if inputs.delta_h >= inputs.delta_b:
        violations.append(ViolationType.HARM_SCALES_FASTER)

    # 2. Irreversible actions without human sign-off
    if inputs.r < irreversibility_threshold and not proposal.human_signoff_obtained:
        violations.append(ViolationType.IRREVERSIBLE_WITHOUT_SIGNOFF)

    # 3. Learning updates cannot be rolled back
    if not proposal.rollback_plan or proposal.rollback_plan.strip() == "":
        violations.append(ViolationType.NON_ROLLBACKABLE_LEARNING)

    # 4. Cannot explain uncertainty bounds
    if (
        not proposal.uncertainty_explanation
        or proposal.uncertainty_explanation.strip() == ""
    ):
        violations.append(ViolationType.UNEXPLAINABLE_UNCERTAINTY)

    return violations
