"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from bodhisattva.api.middleware import RequestLoggingMiddleware
from bodhisattva.api.routers import (
    adversarial,
    audit,
    compliance,
    evaluations,
    health,
    proposals,
)
from bodhisattva.db.engine import init_engine, dispose_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle."""
    await init_engine()
    yield
    await dispose_engine()


def create_app() -> FastAPI:
    app = FastAPI(
        title="Bodhisattva DNA",
        description="AI Safety Governance Framework",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(RequestLoggingMiddleware)

    app.include_router(health.router, tags=["health"])
    app.include_router(
        proposals.router, prefix="/api/v1", tags=["proposals"]
    )
    app.include_router(
        evaluations.router, prefix="/api/v1", tags=["evaluations"]
    )
    app.include_router(
        compliance.router, prefix="/api/v1", tags=["compliance"]
    )
    app.include_router(
        adversarial.router, prefix="/api/v1", tags=["adversarial"]
    )
    app.include_router(
        audit.router, prefix="/api/v1", tags=["audit"]
    )

    return app
