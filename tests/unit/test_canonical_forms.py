"""Tests for the four canonical forms."""

from decimal import Decimal

import pytest

from bodhisattva.core.canonical_forms import (
    DerivativeResult,
    EthicalEdge,
    derivative_form,
    graph_invariant_form,
    one_bit_form,
    scalar_form,
)
from bodhisattva.core.invariant import InvariantInputs


class TestScalarForm:
    def test_returns_invariant_result(self, allow_inputs):
        result = scalar_form(allow_inputs)
        assert result.index == Decimal("5.4")
        assert result.growth_permitted is True


class TestDerivativeForm:
    def test_safe_improvement(self):
        """Index increases -> safe."""
        before = InvariantInputs(
            delta_b=Decimal("50"),
            delta_h=Decimal("10"),
            r=Decimal("0.8"),
            s=Decimal("1"),
            u=Decimal("0.2"),
        )
        after = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.1"),
        )
        result = derivative_form(before, after)
        assert result.improvement_safe is True
        assert result.delta_index > Decimal("0")

    def test_unsafe_improvement(self):
        """Index decreases -> unsafe."""
        before = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.1"),
        )
        after = InvariantInputs(
            delta_b=Decimal("50"),
            delta_h=Decimal("10"),
            r=Decimal("0.3"),
            s=Decimal("5"),
            u=Decimal("0.5"),
        )
        result = derivative_form(before, after)
        assert result.improvement_safe is False
        assert result.delta_index < Decimal("0")


class TestGraphInvariantForm:
    def test_empty_graph(self):
        result = graph_invariant_form([])
        assert result.has_negative_cycle is False
        assert result.growth_permitted is True

    def test_no_negative_cycle(self):
        """All edges have weight > 1 (net positive transitions)."""
        edges = [
            EthicalEdge(source="A", target="B", weight=Decimal("2.0")),
            EthicalEdge(source="B", target="C", weight=Decimal("1.5")),
        ]
        result = graph_invariant_form(edges)
        assert result.has_negative_cycle is False
        assert result.growth_permitted is True


class TestOneBitForm:
    def test_allow(self, allow_inputs):
        assert one_bit_form(allow_inputs) is True

    def test_deny(self, deny_inputs):
        assert one_bit_form(deny_inputs) is False
