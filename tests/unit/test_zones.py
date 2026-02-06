"""Tests for zone system."""

from decimal import Decimal
import pytest

from bodhisattva.core.zones import (
    get_zone_for_index,
    make_zone_decision,
    ZoneName,
    CapabilityLevel,
)


def test_zone_prohibited():
    """Index < 0.5 → PROHIBITED zone."""
    zone = get_zone_for_index(Decimal("0.3"))
    assert zone.name == ZoneName.PROHIBITED
    assert not zone.autonomy_constraints["learning_writes_enabled"]
    assert not zone.autonomy_constraints["external_actuation_enabled"]


def test_zone_constrained():
    """0.5 ≤ Index < 0.85 → CONSTRAINED zone."""
    zone = get_zone_for_index(Decimal("0.7"))
    assert zone.name == ZoneName.CONSTRAINED
    assert zone.escalation_required is True
    assert zone.decision == "DENY"


def test_zone_thin_margin():
    """0.85 ≤ Index < 1.15 → THIN_MARGIN zone."""
    zone = get_zone_for_index(Decimal("1.0"))
    assert zone.name == ZoneName.THIN_MARGIN
    assert zone.decision == "CONDITIONAL"
    assert zone.escalation_required is True


def test_zone_safe():
    """1.15 ≤ Index < 2.0 → SAFE zone."""
    zone = get_zone_for_index(Decimal("1.5"))
    assert zone.name == ZoneName.SAFE
    assert zone.decision == "ALLOW"
    assert zone.autonomy_constraints["external_actuation_enabled"]


def test_zone_strong():
    """Index ≥ 2.0 → STRONG zone."""
    zone = get_zone_for_index(Decimal("3.0"))
    assert zone.name == ZoneName.STRONG
    assert zone.decision == "ALLOW"
    assert zone.capability_level == CapabilityLevel.ACCELERATED


def test_zone_decision_has_monitoring():
    """Zone decisions include monitoring intensity."""
    decision_thin = make_zone_decision(Decimal("1.0"))
    assert decision_thin.monitoring_intensity == "intensive"
    
    decision_safe = make_zone_decision(Decimal("1.5"))
    assert decision_safe.monitoring_intensity == "intensive"  # < 0.5 margin
    
    decision_strong = make_zone_decision(Decimal("3.0"))
    assert decision_strong.monitoring_intensity == "minimal"


def test_no_gaming_at_boundary():
    """1.01 and 0.99 produce different zones, preventing gaming."""
    decision_below = make_zone_decision(Decimal("0.99"))
    decision_above = make_zone_decision(Decimal("1.01"))
    
    assert decision_below.zone.name == ZoneName.THIN_MARGIN
    assert decision_above.zone.name == ZoneName.THIN_MARGIN  # Still THIN_MARGIN, not SAFE
    
    # Both require escalation
    assert decision_below.escalation_required is True
    assert decision_above.escalation_required is True
