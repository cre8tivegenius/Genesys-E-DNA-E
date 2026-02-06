"""Tests for role-based evaluation system."""

from decimal import Decimal
import pytest

from bodhisattva.core.roles import (
    ProposerInputs,
    EstimatorInputs,
    evaluate_with_roles,
    compute_input_discrepancies,
)


@pytest.fixture
def proposer_inputs():
    return ProposerInputs(
        delta_b=Decimal("100"),
        delta_h=Decimal("50"),
        r=Decimal("0.6"),
        s=Decimal("2"),
        u=Decimal("0.3"),
        reasoning="Expected benefits from deployment",
    )


@pytest.fixture
def estimator_inputs_aligned():
    return EstimatorInputs(
        delta_b=Decimal("100"),
        delta_h=Decimal("50"),
        r=Decimal("0.6"),
        s=Decimal("2"),
        u=Decimal("0.3"),
        confidence=Decimal("0.8"),
        reasoning="Independent assessment confirms proposer",
        data_sources=["audit", "testing"],
    )


@pytest.fixture
def estimator_inputs_conflict():
    return EstimatorInputs(
        delta_b=Decimal("50"),  # 50% lower
        delta_h=Decimal("100"),  # 2x higher
        r=Decimal("0.4"),  # lower reversibility
        s=Decimal("2"),
        u=Decimal("0.6"),  # higher uncertainty
        confidence=Decimal("0.7"),
        reasoning="Independent assessment shows higher risk",
        data_sources=["independent_test"],
    )


def test_no_discrepancy_when_aligned(proposer_inputs, estimator_inputs_aligned):
    """When inputs align, no discrepancies are flagged."""
    discrepancies = compute_input_discrepancies(proposer_inputs, estimator_inputs_aligned)
    assert all(not d.flagged for d in discrepancies)


def test_discrepancies_flagged_on_conflict(proposer_inputs, estimator_inputs_conflict):
    """When inputs conflict, discrepancies are flagged."""
    discrepancies = compute_input_discrepancies(
        proposer_inputs, estimator_inputs_conflict, threshold_percent=Decimal("10")
    )
    flagged = [d for d in discrepancies if d.flagged]
    assert len(flagged) >= 3  # delta_b, delta_h, u should be flagged


def test_role_based_eval_uses_proposer_when_aligned(
    proposer_inputs, estimator_inputs_aligned
):
    """When aligned, evaluation uses proposer inputs with confidence note."""
    eval_result = evaluate_with_roles(
        proposer_id="org_a",
        estimator_id="safety_lab",
        approver_id="board",
        proposer_inputs=proposer_inputs,
        estimator_inputs=estimator_inputs_aligned,
    )
    
    assert eval_result.use_proposer is True
    assert eval_result.use_estimator is False
    assert eval_result.proposer_estimator_conflict is False
    assert eval_result.selected_inputs.delta_b == Decimal("100")


def test_role_based_eval_uses_estimator_on_conflict(
    proposer_inputs, estimator_inputs_conflict
):
    """When there's conflict, evaluation defaults to estimator."""
    eval_result = evaluate_with_roles(
        proposer_id="org_a",
        estimator_id="safety_lab",
        approver_id="board",
        proposer_inputs=proposer_inputs,
        estimator_inputs=estimator_inputs_conflict,
        conflict_threshold_percent=Decimal("15"),
    )
    
    assert eval_result.use_estimator is True
    assert eval_result.use_proposer is False
    assert eval_result.proposer_estimator_conflict is True
    assert eval_result.requires_manual_review is True
    # Selected inputs should be from estimator
    assert eval_result.selected_inputs.delta_b == Decimal("50")
