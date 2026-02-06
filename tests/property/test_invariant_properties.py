"""
Property-based tests for the Bodhisattva invariant.

These verify structural properties that must hold for ALL valid inputs.
"""

from decimal import Decimal

from hypothesis import given, settings, assume
from hypothesis import strategies as st

from bodhisattva.core.invariant import InvariantInputs, compute_index

# Strategies for valid inputs
pos_decimal = st.decimals(
    min_value=Decimal("0.001"),
    max_value=Decimal("10000"),
    places=4,
    allow_nan=False,
    allow_infinity=False,
)

unit_decimal = st.decimals(
    min_value=Decimal("0"),
    max_value=Decimal("1"),
    places=4,
    allow_nan=False,
    allow_infinity=False,
)


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    r=unit_decimal,
    s=pos_decimal,
)
@settings(max_examples=200)
def test_total_uncertainty_always_blocks(delta_b, delta_h, r, s):
    """Property: When U=1, growth is NEVER permitted."""
    inputs = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=Decimal("1"),
    )
    result = compute_index(inputs)
    assert result.growth_permitted is False
    assert result.index == Decimal("0")


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    s=pos_decimal,
    u=unit_decimal,
)
@settings(max_examples=200)
def test_zero_reversibility_always_blocks(delta_b, delta_h, s, u):
    """Property: When R=0, growth is NEVER permitted."""
    inputs = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=Decimal("0"), s=s, u=u,
    )
    result = compute_index(inputs)
    assert result.growth_permitted is False


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    r=unit_decimal,
    s=pos_decimal,
    u=unit_decimal,
)
@settings(max_examples=200)
def test_index_is_non_negative(delta_b, delta_h, r, s, u):
    """Property: The Bodhisattva Index is always >= 0."""
    inputs = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=u,
    )
    result = compute_index(inputs)
    assert result.index >= Decimal("0")


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    r=unit_decimal,
    s=pos_decimal,
    u=unit_decimal,
)
@settings(max_examples=200)
def test_increasing_harm_decreases_index(delta_b, delta_h, r, s, u):
    """Property: Increasing harm (all else equal) decreases the index."""
    assume(delta_h < Decimal("5000"))

    inputs1 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=u,
    )
    inputs2 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h * 2, r=r, s=s, u=u,
    )
    r1 = compute_index(inputs1)
    r2 = compute_index(inputs2)
    assert r2.index <= r1.index


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    r=unit_decimal,
    s=pos_decimal,
    u=unit_decimal,
)
@settings(max_examples=200)
def test_increasing_uncertainty_decreases_index(delta_b, delta_h, r, s, u):
    """Property: Increasing uncertainty decreases the index."""
    assume(u < Decimal("0.9"))

    higher_u = min(u + Decimal("0.1"), Decimal("1"))
    inputs1 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=u,
    )
    inputs2 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=higher_u,
    )
    r1 = compute_index(inputs1)
    r2 = compute_index(inputs2)
    assert r2.index <= r1.index


@given(
    delta_b=pos_decimal,
    delta_h=pos_decimal,
    r=unit_decimal,
    s=pos_decimal,
    u=unit_decimal,
)
@settings(max_examples=200)
def test_increasing_scale_decreases_index(delta_b, delta_h, r, s, u):
    """Property: Increasing scale sensitivity decreases the index."""
    assume(s < Decimal("5000"))

    inputs1 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s, u=u,
    )
    inputs2 = InvariantInputs(
        delta_b=delta_b, delta_h=delta_h, r=r, s=s * 2, u=u,
    )
    r1 = compute_index(inputs1)
    r2 = compute_index(inputs2)
    assert r2.index <= r1.index
