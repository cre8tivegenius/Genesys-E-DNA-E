"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from bodhisattva.config import Settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


async def init_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create and cache the async engine."""
    global _engine, _session_factory

    if settings is None:
        settings = Settings()

    _engine = create_async_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
    )
    _session_factory = async_sessionmaker(
        _engine, class_=AsyncSession, expire_on_commit=False
    )
    return _engine


async def dispose_engine() -> None:
    """Dispose the cached engine."""
    global _engine, _session_factory
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_factory = None


def get_engine() -> AsyncEngine:
    """Get the cached engine. Raises if not initialized."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get the cached session factory."""
    if _session_factory is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency-injectable session generator."""
    factory = get_session_factory()
    async with factory() as session:
        yield session
