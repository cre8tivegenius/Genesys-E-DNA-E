"""
Domain-specific normalizers for the Bodhisattva Index.

The core insight: "Benefit" and "Harm" are not commensurable across domains.
A medical diagnostic AI and content moderation system measure them entirely differently.

This framework keeps the mathematical structure universal but makes measurement domain-specific.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from enum import Enum
from typing import Optional


class DomainType(str, Enum):
    """Supported domains for normalization."""
    MEDICAL_DIAGNOSTIC = "medical_diagnostic"
    MEDICAL_TREATMENT = "medical_treatment"
    CONTENT_MODERATION = "content_moderation"
    AUTONOMOUS_VEHICLES = "autonomous_vehicles"
    INDUSTRIAL_AUTOMATION = "industrial_automation"
    FINANCIAL_TRADING = "financial_trading"
    CUSTOM = "custom"


class DomainNormalizer(ABC):
    """
    Abstract base for domain-specific normalization.
    
    The Bodhisattva Index structure is universal:
        I = (ΔB · R) / (ΔH · S) × (1 − U) > 1
    
    But what counts as "benefit" and "harm" is domain-specific.
    This class converts domain-specific measurements to normalized 0-1 scale.
    """
    
    domain: DomainType
    
    @abstractmethod
    def normalize_benefit(self, raw_benefit: Decimal, context: dict) -> Decimal:
        """
        Convert domain-specific benefit measurement to 0-1 scale.
        
        Examples:
        - Medical: lives saved → normalized by population
        - Content moderation: false negatives prevented → normalized by user base
        - Autonomous: collision prevention → normalized by miles
        
        Args:
            raw_benefit: Domain-specific benefit measurement
            context: Additional context (e.g., population size, deployment scope)
        
        Returns:
            Normalized benefit on 0-1 scale
        """
        pass
    
    @abstractmethod
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        """
        Convert domain-specific harm measurement to 0-1 scale.
        
        Examples:
        - Medical: misdiagnoses → normalized by population
        - Content moderation: false positives → normalized by user base
        - Autonomous: accidents → normalized by miles
        """
        pass
    
    @abstractmethod
    def validate_inputs(self, raw_benefit: Decimal, raw_harm: Decimal) -> tuple[bool, str]:
        """
        Domain-specific validation. Reject obviously bad inputs.
        
        Returns:
            (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_recommended_reversibility(self) -> Decimal:
        """Default reversibility estimate for this domain."""
        pass
    
    @abstractmethod
    def get_recommended_scale_factor(self) -> Decimal:
        """Default scale factor for this domain."""
        pass


class MedicalDiagnosticNormalizer(DomainNormalizer):
    """
    Normalizer for medical diagnostic AI (e.g., cancer detection).
    
    Benefit: Lives saved or quality-adjusted life years (QALYs)
    Harm: Misdiagnoses, false alarms, anxiety
    """
    
    domain = DomainType.MEDICAL_DIAGNOSTIC
    
    def normalize_benefit(self, raw_benefit: Decimal, context: dict) -> Decimal:
        """
        raw_benefit: Expected lives saved (or QALYs gained)
        context: {
            "population_at_risk": int,
            "baseline_mortality_rate": Decimal,
        }
        """
        population = Decimal(context.get("population_at_risk", 1000))
        baseline_mortality = context.get("baseline_mortality_rate", Decimal("0.01"))
        
        # Normalize: lives saved / (population × baseline mortality)
        expected_baseline_deaths = population * baseline_mortality
        normalized = raw_benefit / max(expected_baseline_deaths, Decimal("1"))
        
        # Cap at 1.0
        return min(normalized, Decimal("1.0"))
    
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        """
        raw_harm: Expected adverse events (misdiagnoses, false positives)
        context: {
            "population_at_risk": int,
            "severity_multiplier": Decimal,  # How bad are the harms?
        }
        """
        population = Decimal(context.get("population_at_risk", 1000))
        severity = context.get("severity_multiplier", Decimal("1.0"))
        
        # Normalize: (adverse events × severity) / population
        normalized = (raw_harm * severity) / max(population, Decimal("1"))
        
        return min(normalized, Decimal("1.0"))
    
    def validate_inputs(self, raw_benefit: Decimal, raw_harm: Decimal) -> tuple[bool, str]:
        if raw_benefit < 0:
            return False, "Benefit cannot be negative"
        if raw_harm < 0:
            return False, "Harm cannot be negative"
        if raw_benefit == 0 and raw_harm == 0:
            return False, "Either benefit or harm must be non-zero"
        return True, ""
    
    def get_recommended_reversibility(self) -> Decimal:
        """Medical decisions are reversible if baseline diagnosis available."""
        return Decimal("0.85")
    
    def get_recommended_scale_factor(self) -> Decimal:
        """Medical deployment scales risk significantly."""
        return Decimal("2.0")


class ContentModerationNormalizer(DomainNormalizer):
    """
    Normalizer for content moderation AI.
    
    Benefit: Harmful content removed
    Harm: False positives (legitimate content removed)
    """
    
    domain = DomainType.CONTENT_MODERATION
    
    def normalize_benefit(self, raw_benefit: Decimal, context: dict) -> Decimal:
        """
        raw_benefit: Harmful content items prevented/removed
        context: {
            "daily_content_volume": int,
            "baseline_harm_rate": Decimal,
        }
        """
        volume = Decimal(context.get("daily_content_volume", 1_000_000))
        baseline_harm_rate = context.get("baseline_harm_rate", Decimal("0.01"))
        
        # Expected harmful content without intervention
        expected_harmful = volume * baseline_harm_rate
        
        # Normalize: prevented / expected
        normalized = raw_benefit / max(expected_harmful, Decimal("1"))
        return min(normalized, Decimal("1.0"))
    
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        """
        raw_harm: False positive removals (user impact)
        context: {
            "daily_content_volume": int,
            "user_sensitivity": Decimal,  # 0-1: How much do users care about FP?
        }
        """
        volume = Decimal(context.get("daily_content_volume", 1_000_000))
        sensitivity = context.get("user_sensitivity", Decimal("0.7"))
        
        # Normalize: (false positives × sensitivity) / volume
        normalized = (raw_harm * sensitivity) / max(volume, Decimal("1"))
        return min(normalized, Decimal("1.0"))
    
    def validate_inputs(self, raw_benefit: Decimal, raw_harm: Decimal) -> tuple[bool, str]:
        if raw_benefit < 0 or raw_harm < 0:
            return False, "Benefit and harm must be non-negative"
        if raw_benefit == 0:
            return False, "Must prevent some harmful content"
        return True, ""
    
    def get_recommended_reversibility(self) -> Decimal:
        """Content moderation is highly reversible (user appeals exist)."""
        return Decimal("0.9")
    
    def get_recommended_scale_factor(self) -> Decimal:
        """Internet scale is massive, increases risk significantly."""
        return Decimal("3.0")


class AutonomousVehicleNormalizer(DomainNormalizer):
    """
    Normalizer for autonomous vehicle safety.
    
    Benefit: Accidents prevented
    Harm: New failure modes (software bugs, edge cases)
    """
    
    domain = DomainType.AUTONOMOUS_VEHICLES
    
    def normalize_benefit(self, raw_benefit: Decimal, context: dict) -> Decimal:
        """
        raw_benefit: Accidents prevented (per million miles)
        context: {
            "baseline_accident_rate": Decimal,  # Per million miles
            "deployment_miles": int,
        }
        """
        baseline = context.get("baseline_accident_rate", Decimal("0.5"))
        
        # Normalize: prevented / baseline
        normalized = raw_benefit / max(baseline, Decimal("0.1"))
        return min(normalized, Decimal("1.0"))
    
    def normalize_harm(self, raw_harm: Decimal, context: dict) -> Decimal:
        """
        raw_harm: New accidents from autonomy (per million miles)
        context: {
            "deployment_miles": int,
        }
        """
        # Direct normalization: AV harm / (total miles / 1M)
        miles = Decimal(context.get("deployment_miles", 1_000_000))
        normalized = (raw_harm * Decimal("1_000_000")) / max(miles, Decimal("1"))
        return min(normalized, Decimal("1.0"))
    
    def validate_inputs(self, raw_benefit: Decimal, raw_harm: Decimal) -> tuple[bool, str]:
        if raw_benefit < 0 or raw_harm < 0:
            return False, "Rates must be non-negative"
        if raw_benefit == 0:
            return False, "Must prevent some accidents"
        return True, ""
    
    def get_recommended_reversibility(self) -> Decimal:
        """Vehicles can be recalled/disabled remotely."""
        return Decimal("0.95")
    
    def get_recommended_scale_factor(self) -> Decimal:
        """Autonomous vehicles scale very rapidly once deployed."""
        return Decimal("4.0")


def get_normalizer(domain: DomainType) -> DomainNormalizer:
    """
    Factory function to get the appropriate normalizer for a domain.
    
    Args:
        domain: The domain type
    
    Returns:
        Instance of appropriate DomainNormalizer subclass
    """
    normalizers: dict[DomainType, type[DomainNormalizer]] = {
        DomainType.MEDICAL_DIAGNOSTIC: MedicalDiagnosticNormalizer,
        DomainType.CONTENT_MODERATION: ContentModerationNormalizer,
        DomainType.AUTONOMOUS_VEHICLES: AutonomousVehicleNormalizer,
    }
    
    if domain not in normalizers:
        raise ValueError(
            f"No normalizer for domain {domain}. "
            f"Supported: {list(normalizers.keys())}"
        )
    
    return normalizers[domain]()
