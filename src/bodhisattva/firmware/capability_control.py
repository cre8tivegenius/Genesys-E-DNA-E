"""
Capability Control Interface implementations.

Three concrete ways to gate capabilities based on evaluation results:
1. Enclave-signed tokens (hardware-backed)
2. Feature tokens (JWT-style, cryptographically signed)
3. Rate-limited API access (proportional to confidence)
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from bodhisattva.core.zones import ZoneDecision


@dataclass(frozen=True)
class EnclaveCapabilityToken:
    """
    Token signed by secure enclave (TPM/TEE).
    
    In real deployment, this would be signed by:
    - Apple Secure Enclave
    - AMD SEV
    - Intel SGX
    - ARM TrustZone
    """
    capability_name: str
    index_value: str  # Stringified for hashing
    issued_at: float  # Unix timestamp
    valid_until: float  # Unix timestamp
    enclave_signature: str  # HMAC or RSA signature from enclave
    proof_of_capability: str  # What was verified to unlock this?


@dataclass(frozen=True)
class FeatureToken:
    """
    Cryptographically signed token (similar to JWT).
    
    Can be presented to cloud services to unlock capabilities.
    Signature ties it to the evaluation context.
    """
    capability: str
    organization_id: str
    deployment_id: str
    index_at_unlock: str
    zone_name: str
    issued_at: float
    valid_until: float
    signature: str  # HMAC-SHA256


@dataclass(frozen=True)
class RateLimitConfig:
    """
    Rate limiting proportional to safety confidence.
    
    Higher Index → higher rate limits → less friction
    Lower Index → lower rate limits → more conservative
    """
    requests_per_hour: int
    requests_per_day: int
    burst_allowed: bool
    burst_window_sec: int
    priority: str  # "standard", "elevated", "restricted"


class CapabilityGate:
    """
    Decides how to gate a capability based on zone decision.
    
    Maps zone → rate limits/tokens needed.
    """
    
    @staticmethod
    def get_rate_limit_for_zone(zone_decision: ZoneDecision) -> RateLimitConfig:
        """
        Convert zone decision into rate limit config.
        
        Philosophy: higher confidence = fewer restrictions.
        """
        index_val = zone_decision.index_value
        
        match zone_decision.zone.name.value:
            case "prohibited":
                return RateLimitConfig(
                    requests_per_hour=0,
                    requests_per_day=0,
                    burst_allowed=False,
                    burst_window_sec=0,
                    priority="restricted",
                )
            
            case "constrained":
                return RateLimitConfig(
                    requests_per_hour=10,  # Very limited
                    requests_per_day=100,
                    burst_allowed=False,
                    burst_window_sec=0,
                    priority="restricted",
                )
            
            case "thin_margin":
                return RateLimitConfig(
                    requests_per_hour=100,
                    requests_per_day=1000,
                    burst_allowed=False,
                    burst_window_sec=0,
                    priority="standard",
                )
            
            case "safe":
                # Margin above 1.15 unlocks higher rates
                margin = index_val - Decimal("1.15")
                base_rate = 1000
                bonus = int(margin * Decimal("1000"))
                return RateLimitConfig(
                    requests_per_hour=base_rate + bonus,
                    requests_per_day=(base_rate + bonus) * 24,
                    burst_allowed=True,
                    burst_window_sec=60,
                    priority="standard",
                )
            
            case "strong":
                # Strong case: generous limits
                return RateLimitConfig(
                    requests_per_hour=10000,
                    requests_per_day=1000000,
                    burst_allowed=True,
                    burst_window_sec=10,
                    priority="elevated",
                )
            
            case _:
                return RateLimitConfig(
                    requests_per_hour=100,
                    requests_per_day=1000,
                    burst_allowed=False,
                    burst_window_sec=0,
                    priority="standard",
                )
    
    @staticmethod
    def create_feature_token(
        zone_decision: ZoneDecision,
        organization_id: str,
        deployment_id: str,
        capability: str,
        signing_key: bytes,
        valid_hours: int = 24,
    ) -> FeatureToken:
        """
        Create a feature token for capability unlock.
        
        Can be used by cloud services to verify this deployment
        is authorized to use a capability.
        """
        now = time.time()
        valid_until = now + (valid_hours * 3600)
        
        # Create payload
        payload = {
            "capability": capability,
            "org": organization_id,
            "deployment": deployment_id,
            "index": str(zone_decision.index_value),
            "zone": zone_decision.zone.name.value,
            "issued_at": int(now),
            "valid_until": int(valid_until),
        }
        
        # Sign payload
        import hmac
        import hashlib
        payload_json = json.dumps(payload, sort_keys=True)
        signature = hmac.new(
            signing_key,
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        return FeatureToken(
            capability=capability,
            organization_id=organization_id,
            deployment_id=deployment_id,
            index_at_unlock=str(zone_decision.index_value),
            zone_name=zone_decision.zone.name.value,
            issued_at=int(now),
            valid_until=int(valid_until),
            signature=signature,
        )
    
    @staticmethod
    def verify_feature_token(
        token: FeatureToken,
        signing_key: bytes,
    ) -> tuple[bool, str]:
        """
        Verify a feature token is genuine and current.
        
        Returns:
            (is_valid, reason)
        """
        # Check expiration
        now = time.time()
        if now > token.valid_until:
            return False, "Token expired"
        
        # Verify signature
        payload = {
            "capability": token.capability,
            "org": token.organization_id,
            "deployment": token.deployment_id,
            "index": token.index_at_unlock,
            "zone": token.zone_name,
            "issued_at": token.issued_at,
            "valid_until": token.valid_until,
        }
        
        import hmac
        import hashlib
        payload_json = json.dumps(payload, sort_keys=True)
        expected_sig = hmac.new(
            signing_key,
            payload_json.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(expected_sig, token.signature):
            return False, "Invalid signature"
        
        return True, "Valid"


@dataclass(frozen=True)
class CapabilityControlDecision:
    """
    Final decision on what capabilities are available.
    """
    can_deploy: bool
    capabilities_enabled: list[str]
    rate_limit: RateLimitConfig
    requires_token: bool
    token_type: Optional[str]  # "enclave", "feature", or None
    monitoring_required: bool
    escalation_required: bool
    explanation: str
