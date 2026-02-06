"""Adversarial testing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from bodhisattva.api.dependencies import get_adversarial_tester
from bodhisattva.api.schemas import AdversarialTestRequest
from bodhisattva.adversarial.scenarios import AdversarialTester
from bodhisattva.models.adversarial import AdversarialScenario, ResilienceResult

router = APIRouter()


@router.post(
    "/adversarial/test", response_model=list[ResilienceResult]
)
async def run_adversarial_battery(
    request: AdversarialTestRequest,
    tester: AdversarialTester = Depends(get_adversarial_tester),
) -> list[ResilienceResult]:
    """Run the standard adversarial test battery against baseline inputs."""
    return tester.run_standard_battery(request.baseline)


@router.post(
    "/adversarial/scenario", response_model=ResilienceResult
)
async def run_adversarial_scenario(
    scenario: AdversarialScenario,
    tester: AdversarialTester = Depends(get_adversarial_tester),
) -> ResilienceResult:
    """Run a single adversarial scenario."""
    return tester.test_scenario(scenario)
