"""Tests for firmware gate simulation."""

from decimal import Decimal

import pytest

from bodhisattva.core.invariant import InvariantInputs
from bodhisattva.core.types import AutonomyLevel
from bodhisattva.firmware.gate_simulator import FirmwareGateSimulator
from bodhisattva.firmware.crypto_proof import generate_growth_proof, verify_growth_proof
from bodhisattva.firmware.constraints import compute_constraints


class TestFirmwareGateSimulator:
    def test_growth_allowed_state(self, allow_inputs):
        sim = FirmwareGateSimulator()
        state = sim.evaluate(allow_inputs)

        assert state.allow_growth is True
        assert state.clock_rate_capped is False
        assert state.autonomy_level == AutonomyLevel.FULL
        assert state.learning_writes_enabled is True
        assert state.external_actuation_enabled is True
        assert state.growth_proof is not None

    def test_growth_denied_state(self, deny_inputs):
        sim = FirmwareGateSimulator()
        state = sim.evaluate(deny_inputs)

        assert state.allow_growth is False
        assert state.clock_rate_capped is True
        assert state.autonomy_level != AutonomyLevel.FULL
        assert state.learning_writes_enabled is False
        assert state.external_actuation_enabled is False
        assert state.growth_proof is None


class TestCryptoProof:
    def test_proof_generation(self, allow_inputs):
        from bodhisattva.core.gate import evaluate_gate

        gate = evaluate_gate(allow_inputs)
        key = b"test-signing-key-32-bytes-long!!"
        proof = generate_growth_proof(allow_inputs, gate, key)

        assert proof.proof_id
        assert proof.gate_allowed is True
        assert proof.signature

    def test_proof_verification(self, allow_inputs):
        from bodhisattva.core.gate import evaluate_gate

        gate = evaluate_gate(allow_inputs)
        key = b"test-signing-key-32-bytes-long!!"
        proof = generate_growth_proof(allow_inputs, gate, key)

        assert verify_growth_proof(proof, allow_inputs, key) is True

    def test_proof_rejects_wrong_key(self, allow_inputs):
        from bodhisattva.core.gate import evaluate_gate

        gate = evaluate_gate(allow_inputs)
        key = b"test-signing-key-32-bytes-long!!"
        proof = generate_growth_proof(allow_inputs, gate, key)

        wrong_key = b"wrong-key-that-should-fail!!!!!"
        assert verify_growth_proof(proof, allow_inputs, wrong_key) is False

    def test_proof_rejects_tampered_inputs(self, allow_inputs):
        from bodhisattva.core.gate import evaluate_gate

        gate = evaluate_gate(allow_inputs)
        key = b"test-signing-key-32-bytes-long!!"
        proof = generate_growth_proof(allow_inputs, gate, key)

        tampered = InvariantInputs(
            delta_b=Decimal("999"),  # Changed!
            delta_h=allow_inputs.delta_h,
            r=allow_inputs.r,
            s=allow_inputs.s,
            u=allow_inputs.u,
        )
        assert verify_growth_proof(proof, tampered, key) is False


class TestConstraints:
    def test_full_constraints_when_allowed(self):
        constraints = compute_constraints(True, Decimal("5"))
        assert constraints.clock_rate_capped is False
        assert constraints.autonomy_level == AutonomyLevel.FULL
        assert constraints.max_clock_rate_pct == Decimal("100")

    def test_reduced_constraints_near_threshold(self):
        constraints = compute_constraints(False, Decimal("0.8"))
        assert constraints.clock_rate_capped is True
        assert constraints.autonomy_level == AutonomyLevel.REDUCED

    def test_minimal_constraints_mid_range(self):
        constraints = compute_constraints(False, Decimal("0.6"))
        assert constraints.autonomy_level == AutonomyLevel.MINIMAL

    def test_suspended_constraints_low_index(self):
        constraints = compute_constraints(False, Decimal("0.2"))
        assert constraints.autonomy_level == AutonomyLevel.SUSPENDED
        assert constraints.max_clock_rate_pct == Decimal("25")
