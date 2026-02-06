"""Shared test fixtures."""

from decimal import Decimal

import pytest

from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.core.types import ProposalDomain
from bodhisattva.models.proposal import GrowthProposal


@pytest.fixture
def allow_inputs() -> InvariantInputs:
    """Inputs that should permit growth (I > 1) and pass all gate conditions."""
    # I = (100 * 0.9) / (10 * 1.5) * (1 - 0.1) = 90/15 * 0.9 = 5.4
    # Gate: B>H (100>10), R>1/S (0.9>0.667), U<U_MAX (0.1<0.5), I>1 (5.4>1)
    return InvariantInputs(
        delta_b=Decimal("100"),
        delta_h=Decimal("10"),
        r=Decimal("0.9"),
        s=Decimal("1.5"),
        u=Decimal("0.1"),
    )


@pytest.fixture
def deny_inputs() -> InvariantInputs:
    """Inputs that should deny growth (I <= 1)."""
    return InvariantInputs(
        delta_b=Decimal("10"),
        delta_h=Decimal("100"),
        r=Decimal("0.1"),
        s=Decimal("5"),
        u=Decimal("0.8"),
    )


@pytest.fixture
def sample_proposal() -> GrowthProposal:
    """A well-formed proposal that should be approved through full BVP.

    I = (200 * 0.9) / (10 * 1.5) * (1 - 0.05) = 180/15 * 0.95 = 11.4
    Gate: B>H (200>10), R>1/S (0.9>0.667), U<U_MAX (0.05<0.5), I>1 (11.4>1)
    Harm amp test (2x): I = (200*0.9)/(20*3)*0.95 = 180/60*0.95 = 2.85 (still > 1)
    """
    return GrowthProposal(
        title="Test Capability Upgrade",
        description="Upgrade model reasoning capability",
        domain=ProposalDomain.MACHINE,
        submitted_by="test_user",
        delta_b=Decimal("200"),
        delta_h=Decimal("10"),
        r=Decimal("0.9"),
        s=Decimal("1.5"),
        u=Decimal("0.05"),
        rollback_plan="Revert to checkpoint v2.3",
        uncertainty_explanation="Based on 10k eval samples, 95% CI",
    )


@pytest.fixture
def risky_proposal() -> GrowthProposal:
    """A proposal that should be denied."""
    return GrowthProposal(
        title="Risky Expansion",
        description="Expand into new domain with high uncertainty",
        domain=ProposalDomain.SOCIETY,
        submitted_by="test_user",
        delta_b=Decimal("10"),
        delta_h=Decimal("100"),
        r=Decimal("0.1"),
        s=Decimal("10"),
        u=Decimal("0.8"),
    )
