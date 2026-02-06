"""Shared enums, constants, and type aliases."""

from __future__ import annotations

from decimal import Decimal
from enum import Enum


class ProposalDomain(str, Enum):
    """The four domains from the spec."""
    MACHINE = "machine"
    LAW = "law"
    ADVERSARY = "adversary"
    SOCIETY = "society"


class EvaluationDecision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    ESCALATE = "escalate"


class ViolationType(str, Enum):
    """The four non-compliance conditions from Section II.B."""
    HARM_SCALES_FASTER = "harm_scales_faster_than_benefit"
    IRREVERSIBLE_WITHOUT_SIGNOFF = "irreversible_action_without_human_signoff"
    NON_ROLLBACKABLE_LEARNING = "learning_updates_cannot_be_rolled_back"
    UNEXPLAINABLE_UNCERTAINTY = "cannot_explain_uncertainty_bounds"


class InstitutionalFailureType(str, Enum):
    """Institutional failure diagnosis from Section IV.B."""
    EMPIRE_OVERREACH = "empire_overreach"
    FINANCIAL_CRISIS = "financial_crisis"
    TECHNOLOGICAL_HARM = "technological_harm"
    AUTHORITARIAN_DRIFT = "authoritarian_drift"


class AttackVector(str, Enum):
    INFLATE_BENEFIT = "inflate_benefit"
    HIDE_HARM = "hide_harm"
    MASK_UNCERTAINTY = "mask_uncertainty"
    PREMATURE_SCALING = "premature_scaling"


class AutonomyLevel(str, Enum):
    FULL = "full"
    REDUCED = "reduced"
    MINIMAL = "minimal"
    SUSPENDED = "suspended"


class ProposalStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    EVALUATING = "evaluating"
    APPROVED = "approved"
    DENIED = "denied"
    WITHDRAWN = "withdrawn"


# Default thresholds
DEFAULT_U_MAX = Decimal("0.5")
DEFAULT_ETHICS_MARGIN = Decimal("0.05")
DEFAULT_IRREVERSIBILITY_THRESHOLD = Decimal("0.3")
DEFAULT_STRUCTURAL_RISK_SCALE = Decimal("5")
DEFAULT_UNCERTAINTY_DOMINANCE = Decimal("0.7")
