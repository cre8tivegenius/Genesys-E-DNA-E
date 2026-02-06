"""Tests for the one-bit gate logic."""

from decimal import Decimal

import pytest

from bodhisattva.core.gate import evaluate_gate
from bodhisattva.core.invariant import InvariantInputs


class TestGateDecision:
    def test_all_conditions_pass(self, allow_inputs):
        gate = evaluate_gate(allow_inputs)
        assert gate.allow_growth is True
        assert gate.conditions.benefit_exceeds_harm is True
        assert gate.conditions.reversibility_sufficient is True
        assert gate.conditions.uncertainty_acceptable is True
        assert gate.conditions.index_above_threshold is True

    def test_all_conditions_fail(self, deny_inputs):
        gate = evaluate_gate(deny_inputs)
        assert gate.allow_growth is False

    def test_benefit_not_exceeding_harm_blocks(self):
        """delta_B <= delta_H should block even if I > 1."""
        inputs = InvariantInputs(
            delta_b=Decimal("10"),
            delta_h=Decimal("10"),
            r=Decimal("1"),
            s=Decimal("0.1"),  # Very low S to push I > 1
            u=Decimal("0"),
        )
        gate = evaluate_gate(inputs)
        assert gate.conditions.benefit_exceeds_harm is False
        assert gate.allow_growth is False

    def test_insufficient_reversibility_blocks(self):
        """R <= 1/S should block."""
        # With S=2, threshold is R > 0.5
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.4"),  # Below 1/S = 0.5
            s=Decimal("2"),
            u=Decimal("0.1"),
        )
        gate = evaluate_gate(inputs)
        assert gate.conditions.reversibility_sufficient is False
        assert gate.allow_growth is False

    def test_high_uncertainty_blocks(self):
        """U >= U_MAX should block."""
        inputs = InvariantInputs(
            delta_b=Decimal("1000"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.6"),
        )
        gate = evaluate_gate(inputs, u_max=Decimal("0.5"))
        assert gate.conditions.uncertainty_acceptable is False
        assert gate.allow_growth is False

    def test_custom_u_max(self):
        """Custom U_MAX threshold."""
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.6"),
        )
        # With u_max=0.7, U=0.6 is acceptable
        gate = evaluate_gate(inputs, u_max=Decimal("0.7"))
        assert gate.conditions.uncertainty_acceptable is True

    def test_gate_decision_contains_index(self, allow_inputs):
        gate = evaluate_gate(allow_inputs)
        assert gate.index_value == Decimal("5.4")
