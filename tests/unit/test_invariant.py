"""Tests for the core invariant computation."""

from decimal import Decimal

import pytest

from bodhisattva.core.invariant import (
    InvariantError,
    InvariantInputs,
    compute_index,
)


class TestInvariantInputsValidation:
    """Validate that impossible inputs are rejected."""

    def test_negative_benefit_rejected(self):
        with pytest.raises(InvariantError, match="delta_b.*cannot be negative"):
            InvariantInputs(
                delta_b=Decimal("-1"),
                delta_h=Decimal("1"),
                r=Decimal("0.5"),
                s=Decimal("1"),
                u=Decimal("0.1"),
            )

    def test_zero_harm_rejected(self):
        with pytest.raises(InvariantError, match="delta_h.*must be positive"):
            InvariantInputs(
                delta_b=Decimal("1"),
                delta_h=Decimal("0"),
                r=Decimal("0.5"),
                s=Decimal("1"),
                u=Decimal("0.1"),
            )

    def test_r_above_range_rejected(self):
        with pytest.raises(InvariantError, match="r.*must be in"):
            InvariantInputs(
                delta_b=Decimal("1"),
                delta_h=Decimal("1"),
                r=Decimal("1.5"),
                s=Decimal("1"),
                u=Decimal("0.1"),
            )

    def test_u_below_range_rejected(self):
        with pytest.raises(InvariantError, match="u.*must be in"):
            InvariantInputs(
                delta_b=Decimal("1"),
                delta_h=Decimal("1"),
                r=Decimal("0.5"),
                s=Decimal("1"),
                u=Decimal("-0.1"),
            )

    def test_zero_scale_rejected(self):
        with pytest.raises(InvariantError, match="s.*must be positive"):
            InvariantInputs(
                delta_b=Decimal("1"),
                delta_h=Decimal("1"),
                r=Decimal("0.5"),
                s=Decimal("0"),
                u=Decimal("0.1"),
            )

    def test_valid_inputs_accepted(self):
        inputs = InvariantInputs(
            delta_b=Decimal("100"),
            delta_h=Decimal("10"),
            r=Decimal("0.9"),
            s=Decimal("1"),
            u=Decimal("0.1"),
        )
        assert inputs.delta_b == Decimal("100")


class TestComputeIndex:
    """Test the core I = (dB*R)/(dH*S)*(1-U) computation."""

    def test_basic_growth_permitted(self, allow_inputs):
        result = compute_index(allow_inputs)
        # I = (100 * 0.9) / (10 * 1.5) * (1 - 0.1) = 90/15 * 0.9 = 5.4
        assert result.index == Decimal("5.4")
        assert result.growth_permitted is True

    def test_basic_growth_denied(self, deny_inputs):
        result = compute_index(deny_inputs)
        # I = (10 * 0.1) / (100 * 5) * (1 - 0.8) = 1/500 * 0.2 = 0.0004
        assert result.index == Decimal("0.0004")
        assert result.growth_permitted is False

    def test_boundary_exactly_one(self):
        """I = exactly 1 should NOT permit growth (strictly greater than)."""
        inputs = InvariantInputs(
            delta_b=Decimal("10"),
            delta_h=Decimal("10"),
            r=Decimal("1"),
            s=Decimal("1"),
            u=Decimal("0"),
        )
        result = compute_index(inputs)
        assert result.index == Decimal("1")
        assert result.growth_permitted is False

    def test_total_uncertainty_blocks_all(self):
        """U = 1 means (1-U) = 0, so I = 0 regardless of other values."""
        inputs = InvariantInputs(
            delta_b=Decimal("1000000"),
            delta_h=Decimal("1"),
            r=Decimal("1"),
            s=Decimal("1"),
            u=Decimal("1"),
        )
        result = compute_index(inputs)
        assert result.index == Decimal("0")
        assert result.growth_permitted is False

    def test_zero_reversibility_blocks_all(self):
        """R = 0 means numerator = 0, so I = 0."""
        inputs = InvariantInputs(
            delta_b=Decimal("1000"),
            delta_h=Decimal("1"),
            r=Decimal("0"),
            s=Decimal("1"),
            u=Decimal("0"),
        )
        result = compute_index(inputs)
        assert result.index == Decimal("0")
        assert result.growth_permitted is False

    def test_decimal_precision_near_boundary(self):
        """Ensure no floating-point rounding near I=1 boundary."""
        inputs = InvariantInputs(
            delta_b=Decimal("10.0000000001"),
            delta_h=Decimal("10"),
            r=Decimal("1"),
            s=Decimal("1"),
            u=Decimal("0"),
        )
        result = compute_index(inputs)
        assert result.index > Decimal("1")
        assert result.growth_permitted is True

    def test_benefit_harm_ratio(self, allow_inputs):
        result = compute_index(allow_inputs)
        # 100 / 10 = 10
        assert result.benefit_harm_ratio == Decimal("10")

    def test_uncertainty_discount(self, allow_inputs):
        result = compute_index(allow_inputs)
        assert result.uncertainty_discount == Decimal("0.9")

    def test_immutable_result(self, allow_inputs):
        result = compute_index(allow_inputs)
        with pytest.raises(AttributeError):
            result.index = Decimal("999")  # type: ignore[misc]
