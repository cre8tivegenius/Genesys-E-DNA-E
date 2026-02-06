"""
BEV (Benefit-Ethics-Value) Estimation.

First stage of the Bodhisattva Validation Pipeline.
Estimates the benefit-to-ethics value ratio from a proposal.
"""

from __future__ import annotations

from decimal import Decimal

from bodhisattva.models.proposal import GrowthProposal


class BEVEstimator:
    """Estimates the Benefit-Ethics-Value from proposal metadata."""

    def estimate(self, proposal: GrowthProposal) -> dict:
        """
        Estimate BEV from the proposal's stakeholder impacts and inputs.

        Returns a dict with estimation details and a passed flag.
        """
        total_benefit = Decimal("0")
        total_harm = Decimal("0")

        for impact in proposal.stakeholder_impacts:
            total_benefit += impact.benefit_estimate
            total_harm += impact.harm_estimate

        # If no stakeholder impacts, use the proposal's raw values
        if not proposal.stakeholder_impacts:
            total_benefit = proposal.delta_b
            total_harm = proposal.delta_h

        bev_ratio = (
            total_benefit / total_harm if total_harm > 0 else Decimal("0")
        )

        # BEV passes if the ratio suggests benefit outweighs harm
        passed = bev_ratio > Decimal("1")

        return {
            "passed": passed,
            "total_benefit": str(total_benefit),
            "total_harm": str(total_harm),
            "bev_ratio": str(bev_ratio),
            "stakeholder_count": len(proposal.stakeholder_impacts),
        }
