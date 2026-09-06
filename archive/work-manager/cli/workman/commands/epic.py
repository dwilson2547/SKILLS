import typer
from rich.console import Console
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Epic commands")
console = Console()


@app.command("create")
def create_epic(project: str = typer.Option(..., "--project"), title: str = typer.Option(..., "--title"), description: str | None = typer.Option(None, "--description")):
    payload = {"title": title}
    if description:
        payload["description"] = description
    try:
        epic = client.request("POST", f"/projects/{project}/epics", json=payload)
        console.print(f"Created {epic['slug']}: {epic['title']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_epics(project: str | None = typer.Option(None, "--project"), status: str | None = typer.Option(None, "--status")):
    params = {k: v for k, v in {"project": project, "status": status}.items() if v}
    try:
        epics = client.request("GET", "/epics", params=params)
        table = Table(title="Epics")
        for col in ["slug", "title", "status", "project_slug"]:
            table.add_column(col)
        for epic in epics:
            table.add_row(epic["slug"], epic["title"], epic["status"], epic.get("project_slug") or "")
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_epic(slug: str):
    try:
        epic = client.request("GET", f"/epics/{slug}")
        console.print(epic)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
