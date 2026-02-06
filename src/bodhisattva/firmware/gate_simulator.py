"""
Capability Control Interface (formerly "Firmware Gate").

Provides graduated capability escalation based on Bodhisattva Index.
Implements the three mechanisms:
1. Secure enclave signing
2. Token-gated features
3. Rate-limited APIs

This avoids the "firmware" framing that sounds threatening while keeping
the core idea: capabilities are unlocked only with cryptographic proof of safety.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.core.gate import evaluate_gate, GateDecision
from bodhisattva.core.types import DEFAULT_U_MAX
from bodhisattva.firmware.constraints import ConstraintSet, compute_constraints
from bodhisattva.firmware.crypto_proof import generate_growth_proof
from bodhisattva.models.firmware import FirmwareState, GrowthProof


class FirmwareGateSimulator:
    """
    Simulates the hardware/firmware one-bit gate.

    Per spec Section I.A:
    - If ALLOW_GROWTH == false: clock capped, autonomy reduced,
      learning writes disabled, external actuation blocked
    - Capability escalation requires cryptographic proof that I > 1
    """

    def __init__(
        self,
        u_max: Decimal = DEFAULT_U_MAX,
        signing_key: bytes | None = None,
    ):
        self._u_max = u_max
        self._signing_key = signing_key
        self._state: Optional[FirmwareState] = None
        self._constraints: Optional[ConstraintSet] = None
        self._gate_decision: Optional[GateDecision] = None

    def evaluate(self, inputs: InvariantInputs) -> FirmwareState:
        """Evaluate the gate and produce the resulting firmware state."""
        gate = evaluate_gate(inputs, self._u_max)
        self._gate_decision = gate

        proof: Optional[GrowthProof] = None
        if gate.allow_growth:
            proof = generate_growth_proof(inputs, gate, self._signing_key)

        constraints = compute_constraints(gate.allow_growth, gate.index_value)
        self._constraints = constraints

        self._state = FirmwareState(
            allow_growth=gate.allow_growth,
            clock_rate_capped=constraints.clock_rate_capped,
            autonomy_level=constraints.autonomy_level,
            learning_writes_enabled=constraints.learning_writes_enabled,
            external_actuation_enabled=constraints.external_actuation_enabled,
            index_value=gate.index_value,
            growth_proof=proof,
        )
        return self._state

    @property
    def current_state(self) -> Optional[FirmwareState]:
        return self._state

    @property
    def current_constraints(self) -> Optional[ConstraintSet]:
        return self._constraints

    @property
    def gate_decision(self) -> Optional[GateDecision]:
        return self._gate_decision
