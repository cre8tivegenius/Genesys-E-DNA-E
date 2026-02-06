"""
Role-based evaluation system for Bodhisattva governance.

Separates concerns: Proposer (wants to deploy), Estimator (independent assessment),
Approver (makes final decision). This prevents self-attestation with math.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from bodhisattva.core.invariant import InvariantInputs


@dataclass(frozen=True)
class EstimatorInputs:
    """Estimates from an independent evaluator, not the proposer."""
    delta_b: Decimal
    delta_h: Decimal
    r: Decimal
    s: Decimal
    u: Decimal
    confidence: Decimal  # 0-1: How confident is this estimate? (0.5-1.0 range)
    reasoning: str  # Why these specific numbers?
    data_sources: list[str]  # Where did these come from?


@dataclass(frozen=True)
class ProposerInputs:
    """Self-reported estimates from the organization proposing deployment."""
    delta_b: Decimal
    delta_h: Decimal
    r: Decimal
    s: Decimal
    u: Decimal
    reasoning: str


@dataclass(frozen=True)
class InputDiscrepancy:
    """Where proposer and estimator disagree significantly."""
    variable: str
    proposer_value: Decimal
    estimator_value: Decimal
    percent_difference: Decimal
    flagged: bool  # True if difference exceeds threshold


@dataclass(frozen=True)
class RoleBasedEvaluation:
    """
    Complete evaluation with role separation and accountability.
    
    This structure makes it clear who said what, and where conflicts are.
    Regulators can audit backwards: which estimates were trusted, who made them.
    """
    evaluation_id: str = ""
    created_at: datetime = None
    
    # Identifying information
    proposer_id: str = ""  # Organization/system proposing deployment
    estimator_id: str = ""  # Independent evaluator (must be different)
    approver_id: str = ""  # Decision maker (ideally different from proposer)
    
    # Input estimates
    proposer_inputs: ProposerInputs = None
    estimator_inputs: EstimatorInputs = None
    
    # Analysis
    discrepancies: list[InputDiscrepancy] = None
    avg_confidence: Decimal = None
    max_discrepancy_percent: Decimal = None
    
    # Decision about which inputs to use
    use_proposer: bool = False  # True if proposer estimates trusted
    use_estimator: bool = False  # True if estimator estimates trusted
    selected_inputs: InvariantInputs = None  # What we actually evaluate
    
    # Flags
    proposer_estimator_conflict: bool = False  # Should trigger escalation
    requires_manual_review: bool = False
    
    reasoning: str = ""

    def __post_init__(self):
        if not self.evaluation_id:
            object.__setattr__(self, "evaluation_id", str(uuid.uuid4()))
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
        if self.discrepancies is None:
            object.__setattr__(self, "discrepancies", [])


def compute_input_discrepancies(
    proposer: ProposerInputs,
    estimator: EstimatorInputs,
    threshold_percent: Decimal = Decimal("20"),
) -> list[InputDiscrepancy]:
    """
    Find where proposer and estimator diverge significantly.
    
    Args:
        proposer: Proposer's self-reported estimates
        estimator: Independent evaluator's estimates
        threshold_percent: Flag discrepancies > this percent difference
    
    Returns:
        List of InputDiscrepancy objects for each variable
    """
    discrepancies = []
    
    variables = [
        ("delta_b", proposer.delta_b, estimator.delta_b),
        ("delta_h", proposer.delta_h, estimator.delta_h),
        ("r", proposer.r, estimator.r),
        ("s", proposer.s, estimator.s),
        ("u", proposer.u, estimator.u),
    ]
    
    for var_name, prop_val, est_val in variables:
        # Percent difference relative to estimator value
        if est_val != 0:
            percent_diff = abs((prop_val - est_val) / est_val) * Decimal("100")
        else:
            percent_diff = Decimal("100") if prop_val != 0 else Decimal("0")
        
        flagged = percent_diff > threshold_percent
        
        discrepancies.append(
            InputDiscrepancy(
                variable=var_name,
                proposer_value=prop_val,
                estimator_value=est_val,
                percent_difference=percent_diff,
                flagged=flagged,
            )
        )
    
    return discrepancies


def evaluate_with_roles(
    proposer_id: str,
    estimator_id: str,
    approver_id: str,
    proposer_inputs: ProposerInputs,
    estimator_inputs: EstimatorInputs,
    conflict_threshold_percent: Decimal = Decimal("15"),
) -> RoleBasedEvaluation:
    """
    Create a role-based evaluation with accountability.
    
    Key insight: If proposer and estimator strongly disagree, that's a signal
    to escalate or use the independent estimate.
    """
    discrepancies = compute_input_discrepancies(
        proposer_inputs,
        estimator_inputs,
        threshold_percent=conflict_threshold_percent,
    )
    
    flagged_discrepancies = [d for d in discrepancies if d.flagged]
    max_discrepancy = max(d.percent_difference for d in discrepancies)
    
    # Decision logic: use estimator if significant conflict
    conflict_detected = len(flagged_discrepancies) > 0
    
    if conflict_detected:
        # In case of conflict, default to independent estimate
        selected_inputs = InvariantInputs(
            delta_b=estimator_inputs.delta_b,
            delta_h=estimator_inputs.delta_h,
            r=estimator_inputs.r,
            s=estimator_inputs.s,
            u=estimator_inputs.u,
        )
        use_estimator = True
        use_proposer = False
        reasoning = f"Conflict detected in {len(flagged_discrepancies)} variables. Using independent estimator."
    else:
        # No conflict: can use proposer estimates, but mark confidence
        selected_inputs = InvariantInputs(
            delta_b=proposer_inputs.delta_b,
            delta_h=proposer_inputs.delta_h,
            r=proposer_inputs.r,
            s=proposer_inputs.s,
            u=proposer_inputs.u,
        )
        use_proposer = True
        use_estimator = False
        reasoning = (
            f"Proposer and estimator aligned. Using proposer estimates with "
            f"{estimator_inputs.confidence*100:.0f}% confidence from independent review."
        )
    
    avg_confidence = estimator_inputs.confidence
    
    return RoleBasedEvaluation(
        proposer_id=proposer_id,
        estimator_id=estimator_id,
        approver_id=approver_id,
        proposer_inputs=proposer_inputs,
        estimator_inputs=estimator_inputs,
        discrepancies=discrepancies,
        avg_confidence=avg_confidence,
        max_discrepancy_percent=max_discrepancy,
        use_proposer=use_proposer,
        use_estimator=use_estimator,
        selected_inputs=selected_inputs,
        proposer_estimator_conflict=conflict_detected,
        requires_manual_review=conflict_detected or avg_confidence < Decimal("0.7"),
        reasoning=reasoning,
    )
