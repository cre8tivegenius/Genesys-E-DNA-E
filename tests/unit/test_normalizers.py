"""Tests for domain normalizers."""

from decimal import Decimal
import pytest

from bodhisattva.core.normalizers import (
    DomainType,
    get_normalizer,
    MedicalDiagnosticNormalizer,
    ContentModerationNormalizer,
    AutonomousVehicleNormalizer,
)


class TestMedicalNormalizer:
    def test_normalize_benefit(self):
        """Lives saved should normalize relative to population baseline."""
        normalizer = MedicalDiagnosticNormalizer()
        context = {
            "population_at_risk": 10000,
            "baseline_mortality_rate": Decimal("0.1"),
        }
        
        # Expected baseline deaths: 10000 × 0.1 = 1000
        # 100 lives saved → 100/1000 = 0.1 normalized
        benefit = normalizer.normalize_benefit(Decimal("100"), context)
        assert benefit == Decimal("0.1")
    
    def test_normalize_harm(self):
        """Adverse events normalize by population."""
        normalizer = MedicalDiagnosticNormalizer()
        context = {
            "population_at_risk": 10000,
            "severity_multiplier": Decimal("1"),
        }
        
        # 100 adverse events / 10000 population = 0.01 normalized
        harm = normalizer.normalize_harm(Decimal("100"), context)
        assert harm == Decimal("0.01")
    
    def test_validate_rejects_negative(self):
        """Negative inputs should be rejected."""
        normalizer = MedicalDiagnosticNormalizer()
        valid, msg = normalizer.validate_inputs(Decimal("-1"), Decimal("10"))
        assert valid is False


class TestContentModerationNormalizer:
    def test_normalize_benefit(self):
        """Prevented harmful content normalizes by volume."""
        normalizer = ContentModerationNormalizer()
        context = {
            "daily_content_volume": 1000000,
            "baseline_harm_rate": Decimal("0.01"),
        }
        
        # Expected harmful: 1M × 0.01 = 10k
        # 5k prevented → 5k/10k = 0.5 normalized
        benefit = normalizer.normalize_benefit(Decimal("5000"), context)
        assert benefit == Decimal("0.5")
    
    def test_different_reversibility(self):
        """Content moderation should have higher reversibility."""
        med = MedicalDiagnosticNormalizer()
        content = ContentModerationNormalizer()
        
        # Content moderation has user appeals, so higher reversibility
        assert content.get_recommended_reversibility() > med.get_recommended_reversibility()


class TestAutonomousVehicleNormalizer:
    def test_normalize_benefit(self):
        """Accidents prevented normalize against baseline."""
        normalizer = AutonomousVehicleNormalizer()
        context = {
            "baseline_accident_rate": Decimal("0.5"),
            "deployment_miles": 1000000,
        }
        
        # 0.3 accidents per million miles prevented
        # Normalized: 0.3 / 0.5 = 0.6
        benefit = normalizer.normalize_benefit(Decimal("0.3"), context)
        assert benefit == Decimal("0.6")


def test_get_normalizer_factory():
    """Factory should return correct normalizer."""
    med = get_normalizer(DomainType.MEDICAL_DIAGNOSTIC)
    assert isinstance(med, MedicalDiagnosticNormalizer)
    
    content = get_normalizer(DomainType.CONTENT_MODERATION)
    assert isinstance(content, ContentModerationNormalizer)


def test_normalizers_cap_at_one():
    """All normalizers should cap outputs at 1.0."""
    normalizer = MedicalDiagnosticNormalizer()
    context = {"population_at_risk": 100, "baseline_mortality_rate": Decimal("0.01")}
    
    # Try to normalize 10000 lives saved (impossible for 100 people)
    benefit = normalizer.normalize_benefit(Decimal("10000"), context)
    assert benefit <= Decimal("1.0")
