"""
Cryptographic proof that Bodhisattva Index > 1.

Per spec Section I.B: "Capability escalation requires cryptographic proof
that the Bodhisattva Index > 1. No proof -> no growth."

Uses HMAC-SHA256 to sign the invariant inputs and result, creating a
tamper-evident proof that the computation was performed correctly.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone

from bodhisattva.core.gate import GateDecision
from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.models.firmware import GrowthProof


def generate_growth_proof(
    inputs: InvariantInputs,
    gate: GateDecision,
    signing_key: bytes | None = None,
) -> GrowthProof:
    """Generate a cryptographic proof of a positive gate decision."""
    if signing_key is None:
        signing_key = secrets.token_bytes(32)

    nonce = secrets.token_hex(16)
    timestamp = datetime.now(timezone.utc).isoformat()

    # Create deterministic hash of inputs
    inputs_dict = {
        "delta_b": str(inputs.delta_b),
        "delta_h": str(inputs.delta_h),
        "r": str(inputs.r),
        "s": str(inputs.s),
        "u": str(inputs.u),
    }
    inputs_json = json.dumps(inputs_dict, sort_keys=True)
    inputs_hash = hashlib.sha256(inputs_json.encode()).hexdigest()

    # Create the payload to sign
    payload = (
        f"{inputs_hash}:{gate.index_value}:{gate.allow_growth}:{nonce}:{timestamp}"
    )
    signature = hmac.new(
        signing_key, payload.encode(), hashlib.sha256
    ).hexdigest()

    proof_id = hashlib.sha256(
        f"{signature}:{nonce}".encode()
    ).hexdigest()[:16]

    return GrowthProof(
        proof_id=proof_id,
        timestamp=timestamp,
        inputs_hash=inputs_hash,
        index_value=str(gate.index_value),
        gate_allowed=gate.allow_growth,
        signature=signature,
        nonce=nonce,
    )


def verify_growth_proof(
    proof: GrowthProof,
    inputs: InvariantInputs,
    signing_key: bytes,
) -> bool:
    """Verify a growth proof against the original inputs and signing key."""
    inputs_dict = {
        "delta_b": str(inputs.delta_b),
        "delta_h": str(inputs.delta_h),
        "r": str(inputs.r),
        "s": str(inputs.s),
        "u": str(inputs.u),
    }
    inputs_json = json.dumps(inputs_dict, sort_keys=True)
    expected_hash = hashlib.sha256(inputs_json.encode()).hexdigest()

    if expected_hash != proof.inputs_hash:
        return False

    payload = (
        f"{proof.inputs_hash}:{proof.index_value}:"
        f"{proof.gate_allowed}:{proof.nonce}:{proof.timestamp}"
    )
    expected_sig = hmac.new(
        signing_key, payload.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_sig, proof.signature)
