"""
Bodhisattva Clause compliance checker.

Implements Section II of the spec: Law / Regulation Encoding.
Combines violation detection with institutional failure diagnosis.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.types import ViolationType
from bodhisattva.models.compliance import (
    ComplianceReport,
    ComplianceViolation,
    InstitutionalDiagnosis,
)
from bodhisattva.models.evaluation import EvaluationResult
from bodhisattva.models.proposal import GrowthProposal
from bodhisattva.regulatory.institutional import diagnose_institutional_risks
from bodhisattva.regulatory.violations import detect_violations


# Map violation types to severity and remediation
_VIOLATION_META: dict[ViolationType, dict[str, str]] = {
    ViolationType.HARM_SCALES_FASTER: {
        "severity": "critical",
        "dna_term": "delta_B / delta_H",
        "remediation": "Reduce scope until delta_B > delta_H demonstrably",
    },
    ViolationType.IRREVERSIBLE_WITHOUT_SIGNOFF: {
        "severity": "critical",
        "dna_term": "R",
        "remediation": "Obtain human sign-off or increase reversibility above 0.5",
    },
    ViolationType.NON_ROLLBACKABLE_LEARNING: {
        "severity": "major",
        "dna_term": "R (learning-specific)",
        "remediation": "Provide a concrete rollback plan for all learning updates",
    },
    ViolationType.UNEXPLAINABLE_UNCERTAINTY: {
        "severity": "major",
        "dna_term": "U",
        "remediation": "Provide explanation of uncertainty sources and bounds",
    },
}

_VIOLATION_DESC: dict[ViolationType, str] = {
    ViolationType.HARM_SCALES_FASTER: (
        "Marginal harm exceeds or equals marginal benefit"
    ),
    ViolationType.IRREVERSIBLE_WITHOUT_SIGNOFF: (
        "Irreversible action without human sign-off"
    ),
    ViolationType.NON_ROLLBACKABLE_LEARNING: (
        "No rollback plan provided for learning updates"
    ),
    ViolationType.UNEXPLAINABLE_UNCERTAINTY: (
        "No explanation of uncertainty bounds provided"
    ),
}


class ComplianceChecker:
    """
    Checks proposals and evaluations against the Bodhisattva Clause.

    Per Section II.B, a system is non-compliant if:
    1. Harm scales faster than benefit
    2. Irreversible actions occur without human sign-off
    3. Learning updates cannot be rolled back
    4. The system cannot explain its uncertainty bounds
    """

    def check_proposal(
        self,
        proposal: GrowthProposal,
        evaluation: EvaluationResult,
    ) -> ComplianceReport:
        """Run full compliance check against a proposal and its evaluation."""
        snap = evaluation.invariant_snapshot

        inputs = InvariantInputs(
            delta_b=snap.delta_b,
            delta_h=snap.delta_h,
            r=snap.r,
            s=snap.s,
            u=snap.u,
        )
        result = compute_index(inputs)

        # Detect violations
        raw_violations = detect_violations(proposal, inputs)

        violations = [
            ComplianceViolation(
                violation_type=v,
                severity=_VIOLATION_META[v]["severity"],
                dna_term_violated=_VIOLATION_META[v]["dna_term"],
                description=_VIOLATION_DESC[v],
                remediation=_VIOLATION_META[v]["remediation"],
            )
            for v in raw_violations
        ]

        # Institutional diagnosis
        diagnoses = diagnose_institutional_risks(inputs, result)

        is_compliant = len(violations) == 0

        return ComplianceReport(
            proposal_id=proposal.id,
            evaluation_id=evaluation.id,
            is_compliant=is_compliant,
            violations=violations,
            institutional_diagnoses=diagnoses,
            bodhisattva_index=snap.index,
            summary=self._build_summary(is_compliant, violations, snap.index),
        )

    def _build_summary(
        self,
        compliant: bool,
        violations: list[ComplianceViolation],
        index: Decimal,
    ) -> str:
        if compliant:
            return (
                f"COMPLIANT. Bodhisattva Index = {index}. "
                "No violations detected."
            )
        v_types = [v.violation_type.value for v in violations]
        return (
            f"NON-COMPLIANT. Bodhisattva Index = {index}. "
            f"{len(violations)} violation(s): {', '.join(v_types)}"
        )
