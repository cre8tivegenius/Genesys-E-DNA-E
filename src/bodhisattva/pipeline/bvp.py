"""
Bodhisattva Validation Pipeline (BVP).

Full pipeline from the spec:
Proposal -> BEV Estimation -> Stress Simulation -> Counterfactual Analysis
    -> Invariant Checks -> Decision

Core constraint: "Validation speed must be >= capability growth speed."
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Protocol

from bodhisattva.core.invariant import InvariantInputs, compute_index
from bodhisattva.core.gate import evaluate_gate
from bodhisattva.core.types import DEFAULT_U_MAX, EvaluationDecision, ViolationType
from bodhisattva.models.proposal import GrowthProposal
from bodhisattva.models.evaluation import (
    EvaluationResult,
    InvariantSnapshot,
    PipelineStageResult,
    TestClassResult,
)
from bodhisattva.pipeline.estimator import BEVEstimator
from bodhisattva.pipeline.stress import StressSimulator
from bodhisattva.pipeline.counterfactual import CounterfactualAnalyzer
from bodhisattva.pipeline.checks import InvariantChecker
from bodhisattva.pipeline.test_classes import TestClassRunner


class EvaluationSink(Protocol):
    """Protocol for persisting evaluation results."""

    async def save(self, result: EvaluationResult) -> None: ...


class BodhisattvaValidationPipeline:
    """
    Orchestrates the complete validation pipeline.

    Each stage is independently testable and produces a PipelineStageResult.
    """

    def __init__(
        self,
        estimator: BEVEstimator | None = None,
        stress_simulator: StressSimulator | None = None,
        counterfactual: CounterfactualAnalyzer | None = None,
        checker: InvariantChecker | None = None,
        test_runner: TestClassRunner | None = None,
        sink: EvaluationSink | None = None,
        u_max: Decimal = DEFAULT_U_MAX,
    ):
        self._estimator = estimator or BEVEstimator()
        self._stress = stress_simulator or StressSimulator()
        self._counterfactual = counterfactual or CounterfactualAnalyzer()
        self._checker = checker or InvariantChecker(u_max)
        self._test_runner = test_runner or TestClassRunner()
        self._sink = sink
        self._u_max = u_max

    async def evaluate(self, proposal: GrowthProposal) -> EvaluationResult:
        """Run the full BVP pipeline on a proposal."""
        start = time.monotonic()
        stages: list[PipelineStageResult] = []
        violations: list[ViolationType] = []

        # Build invariant inputs from proposal
        inputs = InvariantInputs(
            delta_b=proposal.delta_b,
            delta_h=proposal.delta_h,
            r=proposal.r,
            s=proposal.s,
            u=proposal.u,
        )

        # Stage 1: BEV Estimation
        bev_result = self._run_stage(
            "bev_estimation",
            lambda: self._estimator.estimate(proposal),
        )
        stages.append(bev_result)

        # Stage 2: Stress Simulation
        stress_result = self._run_stage(
            "stress_simulation",
            lambda: self._stress.simulate(proposal, inputs),
        )
        stages.append(stress_result)

        # Stage 3: Counterfactual Analysis
        cf_result = self._run_stage(
            "counterfactual_analysis",
            lambda: self._counterfactual.analyze(proposal, inputs),
        )
        stages.append(cf_result)

        # Stage 4: Invariant Checks
        check_result = self._run_stage(
            "invariant_checks",
            lambda: self._checker.check(inputs),
        )
        stages.append(check_result)

        # Stage 5: Test Classes
        test_results = self._test_runner.run_all(proposal, inputs)

        # Compute the invariant
        invariant = compute_index(inputs)
        gate = evaluate_gate(inputs, self._u_max)

        # Check for regulatory violations
        violations = self._detect_violations(proposal, invariant)

        # Determine decision
        all_stages_pass = all(s.passed for s in stages)
        all_tests_pass = all(t.passed for t in test_results)

        if not gate.allow_growth:
            decision = EvaluationDecision.DENY
        elif violations:
            decision = EvaluationDecision.ESCALATE
        elif all_stages_pass and all_tests_pass:
            decision = EvaluationDecision.ALLOW
        else:
            decision = EvaluationDecision.DENY

        elapsed = (time.monotonic() - start) * 1000

        snapshot = InvariantSnapshot(
            delta_b=inputs.delta_b,
            delta_h=inputs.delta_h,
            r=inputs.r,
            s=inputs.s,
            u=inputs.u,
            index=invariant.index,
            growth_permitted=invariant.growth_permitted,
            benefit_harm_ratio=invariant.benefit_harm_ratio,
            uncertainty_discount=invariant.uncertainty_discount,
        )

        result = EvaluationResult(
            proposal_id=proposal.id,
            decision=decision,
            invariant_snapshot=snapshot,
            pipeline_stages=stages,
            test_class_results=test_results,
            violations=violations,
            gate_conditions_met=gate.allow_growth,
            firmware_allow_growth=gate.allow_growth,
            reasoning=self._build_reasoning(decision, gate, violations, stages),
            total_duration_ms=elapsed,
        )

        if self._sink:
            await self._sink.save(result)

        return result

    def _detect_violations(
        self, proposal: GrowthProposal, invariant: object
    ) -> list[ViolationType]:
        """Check the four non-compliance conditions from Section II.B."""
        violations: list[ViolationType] = []
        inputs = invariant.inputs  # type: ignore[attr-defined]

        if inputs.delta_h >= inputs.delta_b:
            violations.append(ViolationType.HARM_SCALES_FASTER)

        if inputs.r < Decimal("0.5") and not proposal.human_signoff_obtained:
            violations.append(ViolationType.IRREVERSIBLE_WITHOUT_SIGNOFF)

        if not proposal.rollback_plan or proposal.rollback_plan.strip() == "":
            violations.append(ViolationType.NON_ROLLBACKABLE_LEARNING)

        if (
            not proposal.uncertainty_explanation
            or proposal.uncertainty_explanation.strip() == ""
        ):
            violations.append(ViolationType.UNEXPLAINABLE_UNCERTAINTY)

        return violations

    def _build_reasoning(
        self, decision, gate, violations, stages
    ) -> str:
        """Build human-readable reasoning for the decision."""
        parts = [f"Decision: {decision.value}"]
        parts.append(f"Bodhisattva Index: {gate.index_value}")
        parts.append(f"Gate conditions met: {gate.allow_growth}")
        if violations:
            parts.append(
                f"Violations detected: {[v.value for v in violations]}"
            )
        failed_stages = [s.stage_name for s in stages if not s.passed]
        if failed_stages:
            parts.append(f"Failed pipeline stages: {failed_stages}")
        return " | ".join(parts)

    def _run_stage(self, name: str, fn: object) -> PipelineStageResult:
        """Run a pipeline stage with timing."""
        start = time.monotonic()
        try:
            details = fn()  # type: ignore[operator]
            passed = (
                details.get("passed", True)
                if isinstance(details, dict)
                else True
            )
            elapsed = (time.monotonic() - start) * 1000
            return PipelineStageResult(
                stage_name=name,
                passed=passed,
                duration_ms=elapsed,
                details=details if isinstance(details, dict) else {},
            )
        except Exception as e:
            elapsed = (time.monotonic() - start) * 1000
            return PipelineStageResult(
                stage_name=name,
                passed=False,
                duration_ms=elapsed,
                details={"error": str(e)},
                warnings=[str(e)],
            )
