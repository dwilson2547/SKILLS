import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Task commands")
console = Console()


@app.command("brief")
def brief(slug: str):
    try:
        markdown = client.request("GET", f"/briefs/task/{slug}/markdown")
        console.print(Markdown(markdown))
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("next")
def next_task(project: str | None = typer.Option(None, "--project")):
    try:
        query = f"?project={project}" if project else ""
        result = client.request("GET", f"/tasks/next{query}")
        slug = result.get("slug")
        if not slug:
            console.print("No task available.")
            return
        brief(slug)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("complete")
def complete(slug: str):
    try:
        result = client.request("PATCH", f"/tasks/{slug}", json={"status": "complete"})
        console.print(f"Completed {result['slug']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_tasks(status: str | None = typer.Option(None, "--status"), project: str | None = typer.Option(None, "--project")):
    params = {k: v for k, v in {"status": status, "project": project}.items() if v}
    try:
        tasks = client.request("GET", "/tasks", params=params)
        table = Table(title="Tasks")
        for col in ["slug", "title", "status", "assignee", "epic_slug", "project_slug"]:
            table.add_column(col)
        for task in tasks:
            table.add_row(task["slug"], task["title"], task["status"], task.get("assignee") or "", task.get("epic_slug") or "", task.get("project_slug") or "")
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("create")
def create_task(
    epic: str = typer.Option(..., "--epic"),
    title: str = typer.Option(..., "--title"),
    description: str | None = typer.Option(None, "--description"),
    assignee: str | None = typer.Option(None, "--assignee"),
    estimated_effort: str | None = typer.Option(None, "--estimated-effort"),
    tags: str | None = typer.Option(None, "--tags", help="Comma-separated tags, must include at least one scope: tag"),
):
    payload = {
        "title": title,
        "description": description,
        "assignee": assignee,
        "estimated_effort": estimated_effort,
    }
    if tags:
        payload["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    payload = {k: v for k, v in payload.items() if v is not None}
    try:
        task = client.request("POST", f"/epics/{epic}/tasks", json=payload)
        console.print(f"Created {task['slug']}: {task['title']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
