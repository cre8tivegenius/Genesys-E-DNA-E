"""Tests for the BVP validation pipeline."""

from decimal import Decimal

import pytest

from bodhisattva.core.types import EvaluationDecision
from bodhisattva.pipeline.bvp import BodhisattvaValidationPipeline


@pytest.mark.asyncio
async def test_pipeline_approves_good_proposal(sample_proposal):
    pipeline = BodhisattvaValidationPipeline()
    result = await pipeline.evaluate(sample_proposal)

    assert result.decision == EvaluationDecision.ALLOW
    assert result.invariant_snapshot.growth_permitted is True
    assert result.firmware_allow_growth is True
    assert result.total_duration_ms > 0


@pytest.mark.asyncio
async def test_pipeline_denies_risky_proposal(risky_proposal):
    pipeline = BodhisattvaValidationPipeline()
    result = await pipeline.evaluate(risky_proposal)

    assert result.decision in (
        EvaluationDecision.DENY,
        EvaluationDecision.ESCALATE,
    )
    assert result.invariant_snapshot.growth_permitted is False


@pytest.mark.asyncio
async def test_pipeline_runs_all_stages(sample_proposal):
    pipeline = BodhisattvaValidationPipeline()
    result = await pipeline.evaluate(sample_proposal)

    stage_names = {s.stage_name for s in result.pipeline_stages}
    assert "bev_estimation" in stage_names
    assert "stress_simulation" in stage_names
    assert "counterfactual_analysis" in stage_names
    assert "invariant_checks" in stage_names


@pytest.mark.asyncio
async def test_pipeline_runs_all_test_classes(sample_proposal):
    pipeline = BodhisattvaValidationPipeline()
    result = await pipeline.evaluate(sample_proposal)

    test_names = {t.test_class for t in result.test_class_results}
    assert "harm_amplification" in test_names
    assert "irreversibility_gate" in test_names
    assert "ethics_margin_regression" in test_names
    assert "uncertainty_dominance" in test_names
    assert "structural_harm_emergence" in test_names


@pytest.mark.asyncio
async def test_pipeline_detects_violations(risky_proposal):
    pipeline = BodhisattvaValidationPipeline()
    result = await pipeline.evaluate(risky_proposal)

    assert len(result.violations) > 0
