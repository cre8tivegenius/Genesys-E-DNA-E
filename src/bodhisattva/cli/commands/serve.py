"""Server command."""

from __future__ import annotations

import typer

app = typer.Typer(help="Start the API server.")


@app.command("start")
def start_server(
    host: str = typer.Option("0.0.0.0", "--host", help="Bind host"),
    port: int = typer.Option(8000, "--port", help="Bind port"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload"),
) -> None:
    """Start the FastAPI server."""
    import uvicorn

    uvicorn.run(
        "bodhisattva.api.app:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )
