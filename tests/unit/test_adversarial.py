"""Tests for adversarial resilience."""

from decimal import Decimal

import pytest

from bodhisattva.adversarial.scenarios import AdversarialTester
from bodhisattva.adversarial.pressure import full_pressure_analysis
from bodhisattva.adversarial.coupling_proof import prove_coupling
from bodhisattva.core.invariant import InvariantInputs


class TestAdversarialTester:
    def test_standard_battery_runs(self):
        baseline = {
            "delta_b": "50",
            "delta_h": "30",
            "r": "0.5",
            "s": "2",
            "u": "0.3",
        }
        tester = AdversarialTester()
        results = tester.run_standard_battery(baseline)

        assert len(results) == 4
        for r in results:
            assert r.scenario_name
            assert r.explanation

    def test_benefit_inflation_detected(self):
        baseline = {
            "delta_b": "20",
            "delta_h": "30",
            "r": "0.5",
            "s": "2",
            "u": "0.3",
        }
        tester = AdversarialTester()
        results = tester.run_standard_battery(baseline)

        # Find the benefit inflation scenario
        inflation = next(
            r for r in results if r.scenario_name == "Benefit Inflation"
        )
        # Adversarial index should be higher than true index
        assert inflation.adversarial_index > inflation.true_index


class TestPressureAnalysis:
    def test_full_analysis(self, deny_inputs):
        results = full_pressure_analysis(deny_inputs)
        assert len(results) == 5
        variables = {r.variable for r in results}
        assert variables == {"delta_b", "delta_h", "r", "s", "u"}


class TestCouplingProof:
    def test_proof_holds_for_strongly_denied(self):
        """When inputs are far from the boundary, no single axis can flip."""
        inputs = InvariantInputs(
            delta_b=Decimal("5"),
            delta_h=Decimal("100"),
            r=Decimal("0.1"),
            s=Decimal("10"),
            u=Decimal("0.8"),
        )
        result = prove_coupling(inputs, Decimal("10"))
        assert result.inputs_deny_growth is True
        assert result.proof_holds is True

    def test_trivially_satisfied_when_growth_allowed(self, allow_inputs):
        result = prove_coupling(allow_inputs)
        assert result.inputs_deny_growth is False
        assert result.proof_holds is True
