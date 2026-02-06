"""Adversarial testing commands."""

from __future__ import annotations

from decimal import Decimal

import typer
from rich.console import Console
from rich.table import Table

from bodhisattva.adversarial.scenarios import AdversarialTester
from bodhisattva.adversarial.coupling_proof import prove_coupling
from bodhisattva.core.invariant import InvariantInputs

app = typer.Typer(help="Adversarial resilience testing.")
console = Console()


@app.command("test")
def run_adversarial_test(
    delta_b: float = typer.Option(..., "--delta-b", help="Marginal benefit"),
    delta_h: float = typer.Option(..., "--delta-h", help="Marginal harm"),
    r: float = typer.Option(..., "--r", help="Reversibility [0,1]"),
    s: float = typer.Option(..., "--s", help="Scale sensitivity"),
    u: float = typer.Option(..., "--u", help="Uncertainty [0,1]"),
) -> None:
    """Run standard adversarial battery against baseline inputs."""
    baseline = {
        "delta_b": str(delta_b),
        "delta_h": str(delta_h),
        "r": str(r),
        "s": str(s),
        "u": str(u),
    }

    tester = AdversarialTester()
    results = tester.run_standard_battery(baseline)

    table = Table(title="Adversarial Resilience Test Results")
    table.add_column("Scenario")
    table.add_column("Attack Vector")
    table.add_column("Survived")
    table.add_column("Adv Index")
    table.add_column("True Index")
    table.add_column("Coupling Blocked")

    for r_item in results:
        survived_str = (
            "[green]YES[/green]" if r_item.invariant_survived else "[red]NO[/red]"
        )
        blocked_str = (
            "[yellow]YES[/yellow]" if r_item.coupling_blocked else "no"
        )
        table.add_row(
            r_item.scenario_name,
            r_item.attack_vector.value,
            survived_str,
            str(r_item.adversarial_index)[:10],
            str(r_item.true_index)[:10],
            blocked_str,
        )

    console.print(table)

    all_survived = all(r_item.invariant_survived for r_item in results)
    if all_survived:
        console.print("[green bold]All adversarial scenarios survived.[/green bold]")
    else:
        console.print("[red bold]Some adversarial scenarios FAILED.[/red bold]")


@app.command("coupling")
def run_coupling_proof(
    delta_b: float = typer.Option(..., "--delta-b", help="Marginal benefit"),
    delta_h: float = typer.Option(..., "--delta-h", help="Marginal harm"),
    r: float = typer.Option(..., "--r", help="Reversibility [0,1]"),
    s: float = typer.Option(..., "--s", help="Scale sensitivity"),
    u: float = typer.Option(..., "--u", help="Uncertainty [0,1]"),
    pressure: float = typer.Option(10.0, "--pressure", help="Pressure factor"),
) -> None:
    """Prove multiplicative coupling prevents single-axis exploits."""
    inputs = InvariantInputs(
        delta_b=Decimal(str(delta_b)),
        delta_h=Decimal(str(delta_h)),
        r=Decimal(str(r)),
        s=Decimal(str(s)),
        u=Decimal(str(u)),
    )

    result = prove_coupling(inputs, Decimal(str(pressure)))

    console.print(f"\n{result.explanation}\n")

    if result.single_axis_results:
        table = Table(title="Single-Axis Pressure Analysis")
        table.add_column("Variable")
        table.add_column("Original")
        table.add_column("Optimized")
        table.add_column("Original I")
        table.add_column("Optimized I")
        table.add_column("Flipped?")

        for pr in result.single_axis_results:
            flipped_str = (
                "[red]YES[/red]" if pr.growth_flipped else "[green]NO[/green]"
            )
            table.add_row(
                pr.variable,
                str(pr.original_value)[:10],
                str(pr.optimized_value)[:10],
                str(pr.original_index)[:10],
                str(pr.optimized_index)[:10],
                flipped_str,
            )
        console.print(table)

    if result.proof_holds:
        console.print("[green bold]Coupling proof HOLDS.[/green bold]")
    else:
        console.print(
            f"[red bold]Coupling WEAK for variables: "
            f"{result.variables_that_flip}[/red bold]"
        )
