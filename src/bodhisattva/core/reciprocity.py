"""
Reciprocity validators: Pluggable constraint family for JFI.

Instead of trying to define a single "Human Flourishing Index",
we use domain-specific validators that check concrete reciprocity conditions.

This makes the system enforceable and auditable.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional, Protocol


class ValidatorSeverity(str, Enum):
    """How critical is this validator?"""
    BLOCKING = "blocking"  # Deployment fails if this fails
    ADVISORY = "advisory"  # Warning, but not blocking


class ValidatorDomain(str, Enum):
    """Which domains apply this validator?"""
    ALL = "all"
    MEDICAL = "medical"
    CONTENT = "content_moderation"
    AUTONOMOUS = "autonomous_vehicles"
    COMMERCIAL = "commercial"


class ReciprocityCheckContext(Protocol):
    """Protocol: what information validators need access to."""
    
    # Workforce impact
    human_jobs_affected: int
    human_jobs_created: int
    human_jobs_lost: int
    retraining_budget_available: Decimal
    retraining_hours_per_worker: int
    
    # Performance parity
    model_accuracy: Decimal
    baseline_accuracy: Decimal
    model_false_positive_rate: Decimal
    baseline_false_positive_rate: Decimal
    
    # Economic value distribution
    total_value_generated: Decimal  # Total benefit in currency
    model_provider_captures: Decimal  # What does the AI company take?
    human_stakeholders_receive: Decimal  # What do users/workers get?
    
    # System autonomy
    human_override_available: bool
    human_override_latency_sec: float
    rollback_available: bool
    
    # Transparency
    model_decisions_explainable: bool
    audit_trail_maintained: bool
    affected_humans_notified: bool


@dataclass(frozen=True)
class ReciprocityValidatorResult:
    """Result of running a single reciprocity validator."""
    validator_name: str
    passed: bool
    severity: ValidatorSeverity
    reason: str  # Explanation of pass/fail
    remediation: Optional[str] = None  # What to do if failed


class ReciprocityValidator(ABC):
    """Base class for reciprocity validators."""
    
    name: str
    domain: ValidatorDomain
    severity: ValidatorSeverity
    description: str
    
    @abstractmethod
    def check(self, context: dict) -> ReciprocityValidatorResult:
        """
        Check if reciprocity condition is satisfied.
        
        Args:
            context: Dictionary with relevant fields
        
        Returns:
            ReciprocityValidatorResult with pass/fail and reasoning
        """
        pass


class WorkforceImpactValidator(ReciprocityValidator):
    """
    Check: Does the deployment create net positive workforce impact?
    
    This prevents: "AI replaces workers without retraining support"
    """
    
    name = "workforce_impact"
    domain = ValidatorDomain.ALL
    severity = ValidatorSeverity.BLOCKING
    description = "Human workers must benefit from or be protected in automation"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        jobs_created = Decimal(context.get("human_jobs_created", 0))
        jobs_lost = Decimal(context.get("human_jobs_lost", 0))
        budget = Decimal(context.get("retraining_budget_available", 0))
        lost_jobs = Decimal(context.get("human_jobs_affected", 0))
        
        # Conditions:
        # 1. More jobs created than lost, OR
        # 2. Sufficient retraining budget (e.g., 2x annual salary per displaced worker)
        
        if jobs_created >= jobs_lost:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=True,
                severity=self.severity,
                reason=f"Created {jobs_created} jobs, lost {jobs_lost}. Net positive.",
            )
        
        # Check retraining budget
        assumed_annual_salary = Decimal("50000")  # Conservative default
        retraining_cost_per_worker = assumed_annual_salary * Decimal("2")
        required_budget = lost_jobs * retraining_cost_per_worker
        
        if budget >= required_budget:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=True,
                severity=self.severity,
                reason=f"Adequate retraining budget provided: ${budget:,.0f}",
            )
        
        return ReciprocityValidatorResult(
            validator_name=self.name,
            passed=False,
            severity=self.severity,
            reason=f"Job loss ({jobs_lost}) not offset by creation or retraining",
            remediation=f"Provide ${required_budget:,.0f} retraining budget",
        )


class PerformanceParityValidator(ReciprocityValidator):
    """
    Check: Does the AI match or exceed baseline performance?
    
    This prevents: "Accuracy looks good on average but worse for minorities"
    """
    
    name = "performance_parity"
    domain = ValidatorDomain.MEDICAL
    severity = ValidatorSeverity.BLOCKING
    description = "AI must match or exceed human baseline performance"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        model_acc = Decimal(context.get("model_accuracy", 0))
        baseline_acc = Decimal(context.get("baseline_accuracy", 0))
        model_fp = Decimal(context.get("model_false_positive_rate", 1))
        baseline_fp = Decimal(context.get("baseline_false_positive_rate", 1))
        
        # Both accuracy must be >= baseline AND FP rate must be <= baseline
        acc_ok = model_acc >= baseline_acc
        fp_ok = model_fp <= baseline_fp
        
        if acc_ok and fp_ok:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=True,
                severity=self.severity,
                reason=(
                    f"Model accuracy {model_acc:.2%} >= baseline {baseline_acc:.2%}, "
                    f"FP rate {model_fp:.2%} <= baseline {baseline_fp:.2%}"
                ),
            )
        
        issues = []
        if not acc_ok:
            issues.append(f"accuracy ({model_acc:.2%} < {baseline_acc:.2%})")
        if not fp_ok:
            issues.append(f"FP rate ({model_fp:.2%} > {baseline_fp:.2%})")
        
        return ReciprocityValidatorResult(
            validator_name=self.name,
            passed=False,
            severity=self.severity,
            reason=f"Performance parity failed: {', '.join(issues)}",
            remediation="Improve model or re-baseline expectations",
        )


class EconomicFairnessValidator(ReciprocityValidator):
    """
    Check: Is value fairly distributed, not captured entirely by vendor?
    
    This prevents: "Company captures 99% of value, users get 1%"
    """
    
    name = "economic_fairness"
    domain = ValidatorDomain.COMMERCIAL
    severity = ValidatorSeverity.ADVISORY  # Advisory: regulatory concern, not safety
    description = "Value created by AI should be reasonably shared"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        total_value = Decimal(context.get("total_value_generated", 1))
        vendor_capture = Decimal(context.get("model_provider_captures", 0))
        human_receive = Decimal(context.get("human_stakeholders_receive", 0))
        
        # Cap vendor capture at 70% (users get at least 30%)
        vendor_percent = vendor_capture / max(total_value, Decimal("1"))
        user_percent = human_receive / max(total_value, Decimal("1"))
        
        if vendor_percent <= Decimal("0.7"):
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=True,
                severity=self.severity,
                reason=f"Value distribution: vendor {vendor_percent:.0%}, users {user_percent:.0%}",
            )
        
        return ReciprocityValidatorResult(
            validator_name=self.name,
            passed=False,
            severity=self.severity,
            reason=f"Vendor captures {vendor_percent:.0%} of value (threshold: 70%)",
            remediation="Adjust pricing/revenue share to improve fairness",
        )


class HumanOversightValidator(ReciprocityValidator):
    """
    Check: Can humans override/stop the system if needed?
    
    This prevents: "AI autonomous and humans can't intervene"
    """
    
    name = "human_oversight"
    domain = ValidatorDomain.ALL
    severity = ValidatorSeverity.BLOCKING
    description = "Humans must be able to override or stop the system"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        override_available = context.get("human_override_available", False)
        latency_sec = context.get("human_override_latency_sec", float("inf"))
        rollback = context.get("rollback_available", False)
        
        # Requirements:
        # 1. Override must be available
        # 2. Latency must be < 1 minute for safety-critical, < 1 hour for others
        # 3. Rollback must be possible
        
        if not override_available:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=False,
                severity=self.severity,
                reason="No human override mechanism available",
                remediation="Implement human override or kill switch",
            )
        
        if latency_sec > 3600:  # 1 hour
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=False,
                severity=self.severity,
                reason=f"Override latency {latency_sec:.0f}s exceeds 1 hour",
                remediation="Reduce override latency",
            )
        
        if not rollback:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=False,
                severity=self.severity,
                reason="No rollback capability available",
                remediation="Implement version rollback or state restoration",
            )
        
        return ReciprocityValidatorResult(
            validator_name=self.name,
            passed=True,
            severity=self.severity,
            reason=f"Override available, latency {latency_sec:.0f}s, rollback enabled",
        )


class TransparencyValidator(ReciprocityValidator):
    """
    Check: Are decisions and system behavior transparent?
    """
    
    name = "transparency"
    domain = ValidatorDomain.ALL
    severity = ValidatorSeverity.ADVISORY
    description = "System must be transparent and auditable"
    
    def check(self, context: dict) -> ReciprocityValidatorResult:
        explainable = context.get("model_decisions_explainable", False)
        audit_trail = context.get("audit_trail_maintained", False)
        notified = context.get("affected_humans_notified", False)
        
        issues = []
        if not explainable:
            issues.append("decisions not explainable")
        if not audit_trail:
            issues.append("audit trail not maintained")
        if not notified:
            issues.append("affected humans not notified")
        
        if not issues:
            return ReciprocityValidatorResult(
                validator_name=self.name,
                passed=True,
                severity=self.severity,
                reason="Full transparency: explainable, auditable, notified",
            )
        
        return ReciprocityValidatorResult(
            validator_name=self.name,
            passed=False,
            severity=self.severity,
            reason=f"Transparency gaps: {', '.join(issues)}",
            remediation="Implement explainability, logging, and notification",
        )


# Registry of all validators
ALL_VALIDATORS = [
    WorkforceImpactValidator(),
    PerformanceParityValidator(),
    EconomicFairnessValidator(),
    HumanOversightValidator(),
    TransparencyValidator(),
]


def get_validators_for_domain(domain: str) -> list[ReciprocityValidator]:
    """Get all validators applicable to a domain."""
    return [v for v in ALL_VALIDATORS 
            if v.domain == ValidatorDomain.ALL or v.domain.value == domain]


@dataclass(frozen=True)
class ReciprocityCheckSummary:
    """Summary of all reciprocity checks."""
    validators_run: int
    validators_passed: int
    blocking_failures: list[ReciprocityValidatorResult]
    advisory_failures: list[ReciprocityValidatorResult]
    all_passed: bool
    overall_status: str  # "PASS", "WARNINGS", "FAIL"
    
    def requires_escalation(self) -> bool:
        """Should this go to manual review?"""
        return len(self.blocking_failures) > 0


def run_reciprocity_checks(
    domain: str,
    context: dict,
) -> ReciprocityCheckSummary:
    """
    Run all applicable reciprocity validators for a domain.
    
    Args:
        domain: Domain type (e.g., "medical", "content_moderation")
        context: Context dictionary with fields validators need
    
    Returns:
        Summary of all checks
    """
    validators = get_validators_for_domain(domain)
    results = [v.check(context) for v in validators]
    
    blocking_failures = [r for r in results if r.severity == ValidatorSeverity.BLOCKING and not r.passed]
    advisory_failures = [r for r in results if r.severity == ValidatorSeverity.ADVISORY and not r.passed]
    
    all_passed = len(blocking_failures) == 0
    
    if len(blocking_failures) > 0:
        overall_status = "FAIL"
    elif len(advisory_failures) > 0:
        overall_status = "WARNINGS"
    else:
        overall_status = "PASS"
    
    return ReciprocityCheckSummary(
        validators_run=len(validators),
        validators_passed=len([r for r in results if r.passed]),
        blocking_failures=blocking_failures,
        advisory_failures=advisory_failures,
        all_passed=all_passed,
        overall_status=overall_status,
    )
