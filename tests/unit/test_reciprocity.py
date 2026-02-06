"""Tests for reciprocity validators."""

from decimal import Decimal
import pytest

from bodhisattva.core.reciprocity import (
    WorkforceImpactValidator,
    PerformanceParityValidator,
    EconomicFairnessValidator,
    HumanOversightValidator,
    run_reciprocity_checks,
    ValidatorSeverity,
)


class TestWorkforceImpactValidator:
    def test_pass_when_jobs_created(self):
        """Pass when job creation exceeds job loss."""
        validator = WorkforceImpactValidator()
        context = {
            "human_jobs_created": 100,
            "human_jobs_lost": 50,
            "human_jobs_affected": 50,
            "retraining_budget_available": Decimal("0"),
        }
        
        result = validator.check(context)
        assert result.passed is True
    
    def test_pass_with_retraining_budget(self):
        """Pass when adequate retraining budget provided."""
        validator = WorkforceImpactValidator()
        context = {
            "human_jobs_created": 10,
            "human_jobs_lost": 100,
            "human_jobs_affected": 100,
            "retraining_budget_available": Decimal("10_000_000"),
        }
        
        result = validator.check(context)
        assert result.passed is True
    
    def test_fail_without_offset(self):
        """Fail when job loss not offset."""
        validator = WorkforceImpactValidator()
        context = {
            "human_jobs_created": 10,
            "human_jobs_lost": 100,
            "human_jobs_affected": 100,
            "retraining_budget_available": Decimal("0"),
        }
        
        result = validator.check(context)
        assert result.passed is False
        assert result.severity == ValidatorSeverity.BLOCKING


class TestPerformanceParityValidator:
    def test_pass_when_better_than_baseline(self):
        """Pass when model outperforms baseline."""
        validator = PerformanceParityValidator()
        context = {
            "model_accuracy": Decimal("0.95"),
            "baseline_accuracy": Decimal("0.90"),
            "model_false_positive_rate": Decimal("0.02"),
            "baseline_false_positive_rate": Decimal("0.05"),
        }
        
        result = validator.check(context)
        assert result.passed is True
    
    def test_fail_on_lower_accuracy(self):
        """Fail when model is less accurate."""
        validator = PerformanceParityValidator()
        context = {
            "model_accuracy": Decimal("0.85"),
            "baseline_accuracy": Decimal("0.90"),
            "model_false_positive_rate": Decimal("0.02"),
            "baseline_false_positive_rate": Decimal("0.05"),
        }
        
        result = validator.check(context)
        assert result.passed is False


class TestEconomicFairnessValidator:
    def test_pass_when_fair_split(self):
        """Pass when vendor doesn't capture >70%."""
        validator = EconomicFairnessValidator()
        context = {
            "total_value_generated": Decimal("1000"),
            "model_provider_captures": Decimal("600"),  # 60%
            "human_stakeholders_receive": Decimal("400"),  # 40%
        }
        
        result = validator.check(context)
        assert result.passed is True
    
    def test_fail_on_excessive_capture(self):
        """Fail when vendor captures >70%."""
        validator = EconomicFairnessValidator()
        context = {
            "total_value_generated": Decimal("1000"),
            "model_provider_captures": Decimal("900"),  # 90%
            "human_stakeholders_receive": Decimal("100"),
        }
        
        result = validator.check(context)
        assert result.passed is False
        assert result.severity == ValidatorSeverity.ADVISORY


class TestHumanOversightValidator:
    def test_pass_with_full_oversight(self):
        """Pass when override, latency, and rollback available."""
        validator = HumanOversightValidator()
        context = {
            "human_override_available": True,
            "human_override_latency_sec": 30,
            "rollback_available": True,
        }
        
        result = validator.check(context)
        assert result.passed is True
    
    def test_fail_without_override(self):
        """Fail when no human override."""
        validator = HumanOversightValidator()
        context = {
            "human_override_available": False,
            "human_override_latency_sec": 0,
            "rollback_available": True,
        }
        
        result = validator.check(context)
        assert result.passed is False


def test_run_reciprocity_checks_all_pass():
    """Run all validators for a domain."""
    context = {
        # Workforce
        "human_jobs_created": 100,
        "human_jobs_lost": 50,
        "human_jobs_affected": 50,
        "retraining_budget_available": Decimal("0"),
        # Performance
        "model_accuracy": Decimal("0.95"),
        "baseline_accuracy": Decimal("0.90"),
        "model_false_positive_rate": Decimal("0.02"),
        "baseline_false_positive_rate": Decimal("0.05"),
        # Economic
        "total_value_generated": Decimal("1000"),
        "model_provider_captures": Decimal("600"),
        "human_stakeholders_receive": Decimal("400"),
        # Oversight
        "human_override_available": True,
        "human_override_latency_sec": 30,
        "rollback_available": True,
        # Transparency
        "model_decisions_explainable": True,
        "audit_trail_maintained": True,
        "affected_humans_notified": True,
    }
    
    summary = run_reciprocity_checks("medical", context)
    assert summary.all_passed is True
    assert summary.overall_status == "PASS"


def test_run_reciprocity_checks_with_failures():
    """Detect blocking failures."""
    context = {
        "human_jobs_created": 10,
        "human_jobs_lost": 100,
        "human_jobs_affected": 100,
        "retraining_budget_available": Decimal("0"),
        "human_override_available": False,
        "human_override_latency_sec": 0,
        "rollback_available": False,
    }
    
    summary = run_reciprocity_checks("medical", context)
    assert summary.all_passed is False
    assert len(summary.blocking_failures) > 0
    assert summary.overall_status == "FAIL"
    assert summary.requires_escalation()
