"""Compliance commands."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel

app = typer.Typer(help="Regulatory compliance checks.")
console = Console()


@app.command("check")
def check_compliance(
    proposal_id: str = typer.Option(..., "--proposal-id", help="Proposal UUID"),
    evaluation_id: str = typer.Option(..., "--evaluation-id", help="Evaluation UUID"),
) -> None:
    """Run compliance check (requires running database)."""
    console.print(
        f"[yellow]Compliance check for proposal={proposal_id}, "
        f"evaluation={evaluation_id}[/yellow]"
    )
    console.print(
        "This command requires a running database. "
        "Use 'bodhisattva serve' to start the API server, "
        "then use the /api/v1/compliance/check endpoint."
    )
