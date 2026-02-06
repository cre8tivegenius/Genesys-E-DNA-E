"""Dependency injection for FastAPI."""

from __future__ import annotations

from decimal import Decimal
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from bodhisattva.config import Settings
from bodhisattva.db.engine import get_session
from bodhisattva.db.repository import Repository
from bodhisattva.pipeline.bvp import BodhisattvaValidationPipeline
from bodhisattva.regulatory.compliance import ComplianceChecker
from bodhisattva.adversarial.scenarios import AdversarialTester


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


async def get_repository(
    session: AsyncSession = Depends(get_session),
) -> Repository:
    return Repository(session)


def get_pipeline(
    settings: Settings = Depends(get_settings),
) -> BodhisattvaValidationPipeline:
    return BodhisattvaValidationPipeline(u_max=settings.u_max)


def get_compliance_checker() -> ComplianceChecker:
    return ComplianceChecker()


def get_adversarial_tester() -> AdversarialTester:
    return AdversarialTester()
