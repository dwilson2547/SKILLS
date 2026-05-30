import typer
from rich.console import Console
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Runbook commands")
console = Console()


@app.command("list")
def list_runbooks(
    service: str | None = typer.Option(None, "--service"),
    category: str | None = typer.Option(None, "--category"),
    status: str | None = typer.Option(None, "--status"),
):
    params = {k: v for k, v in {"service": service, "category": category, "status": status}.items() if v}
    try:
        runbooks = client.request("GET", "/runbooks", params=params)
        table = Table(title="Runbooks")
        for col in ["slug", "title", "service", "category", "status"]:
            table.add_column(col)
        for runbook in runbooks:
            table.add_row(runbook["slug"], runbook["title"], runbook["service"], runbook["category"], runbook["status"])
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("brief")
def brief(slug: str):
    try:
        runbook = client.request("GET", f"/runbooks/{slug}")
        console.print(runbook)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("validate")
def validate(slug: str):
    try:
        runbook = client.request("POST", f"/runbooks/{slug}/validate")
        console.print(f"Validated {runbook['slug']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
