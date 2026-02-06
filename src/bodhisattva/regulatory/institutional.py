"""
Institutional failure diagnosis mapping.

From Section IV.B of the spec:

| Failure Type          | DNA Term Violated |
|-----------------------|-------------------|
| Empire overreach      | S ignored         |
| Financial crises      | U hidden          |
| Technological harm    | R ignored         |
| Authoritarian drift   | delta_H discounted|

The invariant predicts failure before collapse.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, InvariantResult
from bodhisattva.core.types import InstitutionalFailureType
from bodhisattva.models.compliance import InstitutionalDiagnosis


def diagnose_institutional_risks(
    inputs: InvariantInputs,
    result: InvariantResult,
) -> list[InstitutionalDiagnosis]:
    """
    Analyze inputs and results for patterns matching known institutional failures.

    Returns diagnoses with confidence levels.
    """
    diagnoses: list[InstitutionalDiagnosis] = []

    # Empire overreach: S is very high but growth is still being attempted
    if inputs.s > Decimal("10"):
        confidence = min(inputs.s / Decimal("20"), Decimal("1"))
        diagnoses.append(InstitutionalDiagnosis(
            failure_type=InstitutionalFailureType.EMPIRE_OVERREACH,
            dna_term="S",
            confidence=confidence,
            description=(
                f"Scale sensitivity S={inputs.s} is very high. "
                "Pattern matches empire overreach: scaling without "
                "accounting for scale effects."
            ),
        ))

    # Financial crises: U is high but being downplayed
    if inputs.u > Decimal("0.6"):
        confidence = inputs.u
        diagnoses.append(InstitutionalDiagnosis(
            failure_type=InstitutionalFailureType.FINANCIAL_CRISIS,
            dna_term="U",
            confidence=confidence,
            description=(
                f"Uncertainty U={inputs.u} is high. "
                "Pattern matches financial crisis: uncertainty hidden "
                "or underestimated."
            ),
        ))

    # Technological harm: R is very low
    if inputs.r < Decimal("0.3"):
        confidence = Decimal("1") - inputs.r
        diagnoses.append(InstitutionalDiagnosis(
            failure_type=InstitutionalFailureType.TECHNOLOGICAL_HARM,
            dna_term="R",
            confidence=confidence,
            description=(
                f"Reversibility R={inputs.r} is very low. "
                "Pattern matches technological harm: irreversibility "
                "ignored in pursuit of capability."
            ),
        ))

    # Authoritarian drift: delta_H is being discounted relative to delta_B
    if inputs.delta_h > inputs.delta_b:
        ratio = inputs.delta_h / inputs.delta_b if inputs.delta_b > 0 else Decimal("10")
        confidence = min(ratio / Decimal("5"), Decimal("1"))
        diagnoses.append(InstitutionalDiagnosis(
            failure_type=InstitutionalFailureType.AUTHORITARIAN_DRIFT,
            dna_term="delta_H",
            confidence=confidence,
            description=(
                f"Harm delta_H={inputs.delta_h} exceeds benefit "
                f"delta_B={inputs.delta_b}. Pattern matches authoritarian "
                "drift: harm to others discounted."
            ),
        ))

    return diagnoses
