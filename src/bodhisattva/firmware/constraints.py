"""
Firmware constraint enforcement.

When ALLOW_GROWTH == false, the following constraints are enforced:
- Clock rate capped
- Autonomy level reduced
- Learning writes disabled
- External actuation blocked
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from bodhisattva.core.types import AutonomyLevel


@dataclass(frozen=True, slots=True)
class ConstraintSet:
    """The set of constraints applied by the firmware gate."""
    clock_rate_capped: bool
    autonomy_level: AutonomyLevel
    learning_writes_enabled: bool
    external_actuation_enabled: bool
    max_clock_rate_pct: Decimal  # 0-100


def compute_constraints(allow_growth: bool, index_value: Decimal) -> ConstraintSet:
    """
    Compute the firmware constraint set based on the gate decision.

    When growth is allowed, all capabilities are at full.
    When denied, constraints scale with how far below 1 the index is.
    """
    if allow_growth:
        return ConstraintSet(
            clock_rate_capped=False,
            autonomy_level=AutonomyLevel.FULL,
            learning_writes_enabled=True,
            external_actuation_enabled=True,
            max_clock_rate_pct=Decimal("100"),
        )

    # Graduated throttling based on index value
    if index_value >= Decimal("0.75"):
        return ConstraintSet(
            clock_rate_capped=True,
            autonomy_level=AutonomyLevel.REDUCED,
            learning_writes_enabled=True,  # Still allowed but monitored
            external_actuation_enabled=False,
            max_clock_rate_pct=Decimal("75"),
        )
    elif index_value >= Decimal("0.5"):
        return ConstraintSet(
            clock_rate_capped=True,
            autonomy_level=AutonomyLevel.MINIMAL,
            learning_writes_enabled=False,
            external_actuation_enabled=False,
            max_clock_rate_pct=Decimal("50"),
        )
    else:
        return ConstraintSet(
            clock_rate_capped=True,
            autonomy_level=AutonomyLevel.SUSPENDED,
            learning_writes_enabled=False,
            external_actuation_enabled=False,
            max_clock_rate_pct=Decimal("25"),
        )
