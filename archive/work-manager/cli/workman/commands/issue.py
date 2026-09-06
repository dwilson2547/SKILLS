import typer
from rich.console import Console
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Issue commands")
console = Console()


@app.command("create")
def create_issue(
    title: str = typer.Option(..., "--title"),
    severity: str = typer.Option(..., "--severity"),
    task: str | None = typer.Option(None, "--task"),
):
    payload = {"title": title, "severity": severity}
    if task:
        payload["task_slug"] = task
    try:
        issue = client.request("POST", "/issues", json=payload)
        console.print(f"Created {issue['slug']}: {issue['title']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get_issue(slug: str):
    try:
        issue = client.request("GET", f"/issues/{slug}")
        console.print(issue)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("resolve")
def resolve_issue(slug: str):
    try:
        issue = client.request("POST", f"/issues/{slug}/resolve")
        console.print(f"Resolved {issue['slug']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_issues(task: str | None = typer.Option(None, "--task"), status: str | None = typer.Option(None, "--status")):
    params = {k: v for k, v in {"task": task, "status": status}.items() if v}
    try:
        issues = client.request("GET", "/issues", params=params)
        table = Table(title="Issues")
        for col in ["slug", "title", "severity", "status", "linked_task_slug"]:
            table.add_column(col)
        for issue in issues:
            table.add_row(issue["slug"], issue["title"], issue["severity"], issue["status"], issue.get("linked_task_slug") or "")
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
