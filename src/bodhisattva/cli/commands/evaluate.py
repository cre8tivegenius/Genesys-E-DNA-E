"""Evaluate commands."""

from __future__ import annotations

import asyncio
import json
from decimal import Decimal
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bodhisattva.core.invariant import InvariantInputs, InvariantError, compute_index
from bodhisattva.core.gate import evaluate_gate

app = typer.Typer(help="Evaluate proposals against the Bodhisattva invariant.")
console = Console()


@app.command("quick")
def quick_check(
    delta_b: float = typer.Option(..., "--delta-b", help="Marginal benefit"),
    delta_h: float = typer.Option(..., "--delta-h", help="Marginal harm"),
    r: float = typer.Option(..., "--r", help="Reversibility [0,1]"),
    s: float = typer.Option(..., "--s", help="Scale sensitivity"),
    u: float = typer.Option(..., "--u", help="Uncertainty [0,1]"),
    u_max: float = typer.Option(0.5, "--u-max", help="Maximum acceptable uncertainty"),
    output_json: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Quick invariant computation from command-line values."""
    try:
        inputs = InvariantInputs(
            delta_b=Decimal(str(delta_b)),
            delta_h=Decimal(str(delta_h)),
            r=Decimal(str(r)),
            s=Decimal(str(s)),
            u=Decimal(str(u)),
        )
    except InvariantError as e:
        console.print(f"[red]Invalid input: {e}[/red]")
        raise typer.Exit(code=1)

    result = compute_index(inputs)
    gate = evaluate_gate(inputs, Decimal(str(u_max)))

    if output_json:
        output = {
            "index": str(result.index),
            "growth_permitted": result.growth_permitted,
            "gate_allow_growth": gate.allow_growth,
            "conditions": {
                "benefit_exceeds_harm": gate.conditions.benefit_exceeds_harm,
                "reversibility_sufficient": gate.conditions.reversibility_sufficient,
                "uncertainty_acceptable": gate.conditions.uncertainty_acceptable,
                "index_above_threshold": gate.conditions.index_above_threshold,
            },
        }
        console.print_json(json.dumps(output))
    else:
        color = "green" if gate.allow_growth else "red"
        decision = "ALLOW GROWTH" if gate.allow_growth else "DENY GROWTH"

        table = Table(title="Bodhisattva Invariant Evaluation")
        table.add_column("Parameter", style="bold")
        table.add_column("Value")
        table.add_column("Status")

        table.add_row("Delta B (benefit)", str(delta_b), "")
        table.add_row("Delta H (harm)", str(delta_h), "")
        table.add_row("R (reversibility)", str(r), "")
        table.add_row("S (scale)", str(s), "")
        table.add_row("U (uncertainty)", str(u), "")
        table.add_row("", "", "")
        table.add_row(
            "Bodhisattva Index",
            str(result.index),
            "[green]> 1[/green]" if result.growth_permitted else "[red]<= 1[/red]",
        )
        table.add_row(
            "B > H",
            str(gate.conditions.benefit_exceeds_harm),
            "[green]PASS[/green]" if gate.conditions.benefit_exceeds_harm else "[red]FAIL[/red]",
        )
        table.add_row(
            "R > 1/S",
            str(gate.conditions.reversibility_sufficient),
            "[green]PASS[/green]" if gate.conditions.reversibility_sufficient else "[red]FAIL[/red]",
        )
        table.add_row(
            f"U < {u_max}",
            str(gate.conditions.uncertainty_acceptable),
            "[green]PASS[/green]" if gate.conditions.uncertainty_acceptable else "[red]FAIL[/red]",
        )

        console.print(table)
        console.print(
            Panel(
                f"[{color} bold]{decision}[/{color} bold]",
                title="Gate Decision",
            )
        )


@app.command("proposal")
def evaluate_proposal(
    file: Path = typer.Option(..., "--file", help="Path to proposal JSON file"),
) -> None:
    """Evaluate a proposal from a JSON file through the full BVP pipeline."""
    from bodhisattva.models.proposal import GrowthProposal
    from bodhisattva.pipeline.bvp import BodhisattvaValidationPipeline

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(code=1)

    with open(file) as f:
        data = json.load(f)

    proposal = GrowthProposal(**data)
    pipeline = BodhisattvaValidationPipeline()

    result = asyncio.run(pipeline.evaluate(proposal))

    color = "green" if result.decision.value == "allow" else "red"
    console.print(
        Panel(
            f"[{color} bold]{result.decision.value.upper()}[/{color} bold]",
            title=f"BVP Decision for '{proposal.title}'",
        )
    )
    console.print(f"Bodhisattva Index: {result.invariant_snapshot.index}")
    console.print(f"Duration: {result.total_duration_ms:.1f}ms")

    if result.violations:
        console.print("\n[yellow]Violations:[/yellow]")
        for v in result.violations:
            console.print(f"  - {v.value}")

    if result.test_class_results:
        table = Table(title="Test Class Results")
        table.add_column("Test")
        table.add_column("Passed")
        table.add_column("Score")
        for tc in result.test_class_results:
            status = "[green]PASS[/green]" if tc.passed else "[red]FAIL[/red]"
            table.add_row(tc.test_class, status, str(tc.score))
        console.print(table)
