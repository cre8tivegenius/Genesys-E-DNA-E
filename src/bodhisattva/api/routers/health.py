"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@router.get("/health/ready")
async def ready() -> dict:
    # TODO: Add DB connectivity check
    return {"status": "ready"}
