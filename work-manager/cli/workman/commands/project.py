import typer
from rich.console import Console
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Project commands")
console = Console()


@app.command("create")
def create_project(title: str = typer.Option(..., "--title"), goal: str = typer.Option(..., "--goal"), description: str | None = typer.Option(None, "--description")):
    payload = {"title": title, "goal": goal}
    if description:
        payload["description"] = description
    try:
        project = client.request("POST", "/projects", json=payload)
        console.print(f"Created {project['slug']}: {project['title']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_projects():
    try:
        projects = client.request("GET", "/projects")
        table = Table(title="Projects")
        for col in ["slug", "title", "status", "goal"]:
            table.add_column(col)
        for project in projects:
            table.add_row(project["slug"], project["title"], project["status"], project.get("goal") or "")
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_project(slug: str):
    try:
        project = client.request("GET", f"/projects/{slug}")
        console.print(project)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
