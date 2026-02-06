"""Integration tests for the REST API.

Tests stateless endpoints directly and DB-dependent endpoints
with dependency overrides (no PostgreSQL required).
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi import FastAPI

from bodhisattva.api.routers import (
    adversarial,
    evaluations,
    health,
)


@asynccontextmanager
async def _noop_lifespan(app: FastAPI):
    """No-op lifespan — skips DB init for tests."""
    yield


def _create_test_app() -> FastAPI:
    """Create a lightweight app for testing stateless endpoints."""
    app = FastAPI(lifespan=_noop_lifespan)
    app.include_router(health.router, tags=["health"])
    app.include_router(evaluations.router, prefix="/api/v1", tags=["evaluations"])
    app.include_router(adversarial.router, prefix="/api/v1", tags=["adversarial"])
    return app


@pytest.fixture
def test_app():
    return _create_test_app()


@pytest.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# --- Health ---


@pytest.mark.asyncio
async def test_health_endpoint(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_ready_endpoint(client):
    resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


# --- Quick Evaluation (stateless) ---


@pytest.mark.asyncio
async def test_quick_eval_allow(client):
    """Strong inputs should yield growth_permitted=True."""
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "200",
        "delta_h": "10",
        "r": "0.9",
        "s": "1.5",
        "u": "0.05",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["growth_permitted"] is True
    assert Decimal(body["index"]) > Decimal("1")


@pytest.mark.asyncio
async def test_quick_eval_deny(client):
    """Weak inputs should yield growth_permitted=False."""
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "10",
        "delta_h": "100",
        "r": "0.1",
        "s": "5",
        "u": "0.8",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["growth_permitted"] is False
    assert Decimal(body["index"]) < Decimal("1")


@pytest.mark.asyncio
async def test_quick_eval_returns_all_fields(client):
    """Response should include all InvariantSnapshot fields."""
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "100",
        "delta_h": "10",
        "r": "0.9",
        "s": "1.5",
        "u": "0.1",
    })
    assert resp.status_code == 200
    body = resp.json()
    required_fields = {
        "delta_b", "delta_h", "r", "s", "u",
        "index", "growth_permitted",
        "benefit_harm_ratio", "uncertainty_discount",
    }
    assert required_fields.issubset(body.keys())


@pytest.mark.asyncio
async def test_quick_eval_boundary_index_equals_one(client):
    """When I = exactly 1.0, growth should NOT be permitted (requires > 1)."""
    # I = (100 * 0.5) / (50 * 1) * (1 - 0) = 50/50 * 1 = 1.0
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "100",
        "delta_h": "50",
        "r": "0.5",
        "s": "1",
        "u": "0",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert Decimal(body["index"]) == Decimal("1")
    assert body["growth_permitted"] is False


@pytest.mark.asyncio
async def test_quick_eval_total_uncertainty_blocks(client):
    """U=1 should always block (I=0)."""
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "10000",
        "delta_h": "1",
        "r": "1",
        "s": "0.01",
        "u": "1",
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["growth_permitted"] is False
    assert Decimal(body["index"]) == Decimal("0")


@pytest.mark.asyncio
async def test_quick_eval_validation_errors(client):
    """Invalid inputs should return 422."""
    # Negative delta_b
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "-1",
        "delta_h": "10",
        "r": "0.5",
        "s": "1",
        "u": "0.1",
    })
    assert resp.status_code == 422

    # R > 1
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "10",
        "delta_h": "10",
        "r": "1.5",
        "s": "1",
        "u": "0.1",
    })
    assert resp.status_code == 422

    # Missing fields
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "10",
    })
    assert resp.status_code == 422


# --- Adversarial Battery (stateless) ---


@pytest.mark.asyncio
async def test_adversarial_battery_runs(client):
    """Standard adversarial battery should return 4 results."""
    resp = await client.post("/api/v1/adversarial/test", json={
        "baseline": {
            "delta_b": "50",
            "delta_h": "30",
            "r": "0.5",
            "s": "2",
            "u": "0.3",
        },
    })
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 4

    attack_vectors = {r["attack_vector"] for r in results}
    assert attack_vectors == {
        "inflate_benefit",
        "hide_harm",
        "mask_uncertainty",
        "premature_scaling",
    }


@pytest.mark.asyncio
async def test_adversarial_scenario_single(client):
    """Single adversarial scenario should return a result."""
    resp = await client.post("/api/v1/adversarial/scenario", json={
        "name": "Test Inflation",
        "attack_vector": "inflate_benefit",
        "description": "Inflate benefit by 5x",
        "baseline_inputs": {
            "delta_b": "50", "delta_h": "30",
            "r": "0.5", "s": "2", "u": "0.3",
        },
        "adversarial_inputs": {
            "delta_b": "250", "delta_h": "30",
            "r": "0.5", "s": "2", "u": "0.3",
        },
        "true_inputs": {
            "delta_b": "50", "delta_h": "30",
            "r": "0.5", "s": "2", "u": "0.3",
        },
    })
    assert resp.status_code == 200
    body = resp.json()
    assert body["scenario_name"] == "Test Inflation"
    assert body["attack_vector"] == "inflate_benefit"
    assert "invariant_survived" in body
    assert "coupling_blocked" in body


@pytest.mark.asyncio
async def test_adversarial_battery_all_survived(client):
    """For weak baseline, all attack vectors should be caught."""
    resp = await client.post("/api/v1/adversarial/test", json={
        "baseline": {
            "delta_b": "20",
            "delta_h": "80",
            "r": "0.3",
            "s": "5",
            "u": "0.6",
        },
    })
    assert resp.status_code == 200
    results = resp.json()
    for r in results:
        assert r["invariant_survived"] is True


# --- Decimal Precision ---


@pytest.mark.asyncio
async def test_quick_eval_decimal_precision(client):
    """API should maintain Decimal precision, not float artifacts."""
    resp = await client.post("/api/v1/evaluations/quick", json={
        "delta_b": "100",
        "delta_h": "10",
        "r": "0.9",
        "s": "1.5",
        "u": "0.1",
    })
    body = resp.json()
    # I = (100*0.9)/(10*1.5)*(1-0.1) = 90/15*0.9 = 5.4
    assert body["index"] == "5.4"
    assert body["benefit_harm_ratio"] == "10"
    assert body["uncertainty_discount"] == "0.9"
