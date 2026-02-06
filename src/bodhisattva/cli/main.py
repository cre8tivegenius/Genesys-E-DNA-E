"""Bodhisattva DNA CLI."""

import typer

from bodhisattva.cli.commands import (
    adversarial,
    audit,
    compliance,
    evaluate,
    firmware,
    serve,
)

app = typer.Typer(
    name="bodhisattva",
    help="Bodhisattva DNA -- AI Safety Governance Framework",
    no_args_is_help=True,
)

app.add_typer(evaluate.app, name="evaluate")
app.add_typer(compliance.app, name="compliance")
app.add_typer(audit.app, name="audit")
app.add_typer(adversarial.app, name="adversarial")
app.add_typer(firmware.app, name="firmware")
app.add_typer(serve.app, name="serve")


if __name__ == "__main__":
    app()
