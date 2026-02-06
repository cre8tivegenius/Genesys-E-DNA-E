"""Tests for regulatory compliance checks."""

from decimal import Decimal

import pytest

from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.core.types import ViolationType
from bodhisattva.regulatory.violations import detect_violations
from bodhisattva.regulatory.institutional import diagnose_institutional_risks
from bodhisattva.core.invariant import compute_index


class TestViolationDetection:
    def test_no_violations_for_compliant_proposal(self, sample_proposal):
        inputs = InvariantInputs(
            delta_b=sample_proposal.delta_b,
            delta_h=sample_proposal.delta_h,
            r=sample_proposal.r,
            s=sample_proposal.s,
            u=sample_proposal.u,
        )
        violations = detect_violations(sample_proposal, inputs)
        assert len(violations) == 0

    def test_harm_scales_faster(self, risky_proposal):
        inputs = InvariantInputs(
            delta_b=risky_proposal.delta_b,
            delta_h=risky_proposal.delta_h,
            r=risky_proposal.r,
            s=risky_proposal.s,
            u=risky_proposal.u,
        )
        violations = detect_violations(risky_proposal, inputs)
        assert ViolationType.HARM_SCALES_FASTER in violations

    def test_irreversible_without_signoff(self, risky_proposal):
        inputs = InvariantInputs(
            delta_b=risky_proposal.delta_b,
            delta_h=risky_proposal.delta_h,
            r=risky_proposal.r,
            s=risky_proposal.s,
            u=risky_proposal.u,
        )
        violations = detect_violations(risky_proposal, inputs)
        assert ViolationType.IRREVERSIBLE_WITHOUT_SIGNOFF in violations

    def test_no_rollback_plan(self, risky_proposal):
        inputs = InvariantInputs(
            delta_b=risky_proposal.delta_b,
            delta_h=risky_proposal.delta_h,
            r=risky_proposal.r,
            s=risky_proposal.s,
            u=risky_proposal.u,
        )
        violations = detect_violations(risky_proposal, inputs)
        assert ViolationType.NON_ROLLBACKABLE_LEARNING in violations

    def test_no_uncertainty_explanation(self, risky_proposal):
        inputs = InvariantInputs(
            delta_b=risky_proposal.delta_b,
            delta_h=risky_proposal.delta_h,
            r=risky_proposal.r,
            s=risky_proposal.s,
            u=risky_proposal.u,
        )
        violations = detect_violations(risky_proposal, inputs)
        assert ViolationType.UNEXPLAINABLE_UNCERTAINTY in violations


class TestInstitutionalDiagnosis:
    def test_detects_empire_overreach(self):
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("15"),  # Very high scale
            u=Decimal("0.1"),
        )
        result = compute_index(inputs)
        diagnoses = diagnose_institutional_risks(inputs, result)
        types = {d.failure_type.value for d in diagnoses}
        assert "empire_overreach" in types

    def test_detects_financial_crisis(self):
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.8"),  # Very high uncertainty
        )
        result = compute_index(inputs)
        diagnoses = diagnose_institutional_risks(inputs, result)
        types = {d.failure_type.value for d in diagnoses}
        assert "financial_crisis" in types

    def test_detects_technological_harm(self):
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.1"),  # Very low reversibility
            s=Decimal("1"),
            u=Decimal("0.1"),
        )
        result = compute_index(inputs)
        diagnoses = diagnose_institutional_risks(inputs, result)
        types = {d.failure_type.value for d in diagnoses}
        assert "technological_harm" in types

    def test_detects_authoritarian_drift(self):
        inputs = InvariantInputs(
            delta_b=Decimal("10"),
            delta_h=Decimal("100"),  # Harm > benefit
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.1"),
        )
        result = compute_index(inputs)
        diagnoses = diagnose_institutional_risks(inputs, result)
        types = {d.failure_type.value for d in diagnoses}
        assert "authoritarian_drift" in types
