"""Audit log endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query

from bodhisattva.api.dependencies import get_repository
from bodhisattva.db.repository import Repository

router = APIRouter()


@router.get("/audit/logs")
async def get_audit_logs(
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    proposal_id: Optional[uuid.UUID] = Query(None),
    since: Optional[datetime] = Query(None),
    until: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    repo: Repository = Depends(get_repository),
) -> list[dict]:
    """Query audit logs with optional filters."""
    return await repo.get_audit_logs(
        action=action,
        actor=actor,
        proposal_id=proposal_id,
        since=since,
        until=until,
        limit=size,
        offset=(page - 1) * size,
    )


@router.get("/audit/history/{proposal_id}")
async def get_proposal_history(
    proposal_id: uuid.UUID,
    repo: Repository = Depends(get_repository),
) -> list[dict]:
    """Get full audit history for a specific proposal."""
    return await repo.get_audit_logs(
        proposal_id=proposal_id, limit=200
    )
