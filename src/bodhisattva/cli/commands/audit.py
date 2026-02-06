"""Audit log commands."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console

app = typer.Typer(help="Query audit logs.")
console = Console()


@app.command("logs")
def get_logs(
    action: Optional[str] = typer.Option(None, "--action", help="Filter by action"),
    actor: Optional[str] = typer.Option(None, "--actor", help="Filter by actor"),
    proposal_id: Optional[str] = typer.Option(None, "--proposal-id", help="Filter by proposal"),
    limit: int = typer.Option(50, "--limit", help="Max results"),
) -> None:
    """Query audit logs (requires running database)."""
    console.print("[yellow]Audit log query[/yellow]")
    console.print(
        "This command requires a running database. "
        "Use 'bodhisattva serve' to start the API server, "
        "then use the /api/v1/audit/logs endpoint."
    )


@app.command("history")
def get_history(
    proposal_id: str = typer.Option(..., "--proposal-id", help="Proposal UUID"),
) -> None:
    """Get full audit trail for a proposal (requires running database)."""
    console.print(f"[yellow]Audit history for proposal={proposal_id}[/yellow]")
    console.print(
        "This command requires a running database. "
        "Use 'bodhisattva serve' to start the API server, "
        "then use the /api/v1/audit/history endpoint."
    )
