"""Firmware simulation commands."""

from __future__ import annotations

from decimal import Decimal

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bodhisattva.core.invariant import InvariantInputs, InvariantError
from bodhisattva.firmware.gate_simulator import FirmwareGateSimulator

app = typer.Typer(help="Firmware gate simulation.")
console = Console()


@app.command("simulate")
def simulate_gate(
    delta_b: float = typer.Option(..., "--delta-b", help="Marginal benefit"),
    delta_h: float = typer.Option(..., "--delta-h", help="Marginal harm"),
    r: float = typer.Option(..., "--r", help="Reversibility [0,1]"),
    s: float = typer.Option(..., "--s", help="Scale sensitivity"),
    u: float = typer.Option(..., "--u", help="Uncertainty [0,1]"),
    u_max: float = typer.Option(0.5, "--u-max", help="Maximum uncertainty threshold"),
) -> None:
    """Simulate the firmware gate and show resulting state."""
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

    sim = FirmwareGateSimulator(u_max=Decimal(str(u_max)))
    state = sim.evaluate(inputs)

    color = "green" if state.allow_growth else "red"
    gate_text = "ALLOW GROWTH" if state.allow_growth else "DENY GROWTH"

    console.print(
        Panel(
            f"[{color} bold]{gate_text}[/{color} bold]",
            title="Firmware Gate",
        )
    )

    table = Table(title="Firmware State")
    table.add_column("Parameter", style="bold")
    table.add_column("Value")

    table.add_row("ALLOW_GROWTH", str(state.allow_growth))
    table.add_row("Bodhisattva Index", str(state.index_value))
    table.add_row("Clock Rate Capped", str(state.clock_rate_capped))
    table.add_row("Autonomy Level", state.autonomy_level.value)
    table.add_row("Learning Writes Enabled", str(state.learning_writes_enabled))
    table.add_row("External Actuation Enabled", str(state.external_actuation_enabled))

    if state.growth_proof:
        table.add_row("", "")
        table.add_row("Proof ID", state.growth_proof.proof_id)
        table.add_row("Proof Signature", state.growth_proof.signature[:32] + "...")

    console.print(table)
