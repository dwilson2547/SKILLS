import typer
from rich.console import Console
from rich.table import Table

from ..client import APIError, client

app = typer.Typer(help="Note commands")
console = Console()


def _split_tags(tags: str) -> list[str]:
    return [tag.strip() for tag in tags.split(",") if tag.strip()]


@app.command("add")
def add(title: str = typer.Option(..., "--title"), body: str = typer.Option(..., "--body"), tags: str = typer.Option(..., "--tags")):
    try:
        note = client.request("POST", "/notes", json={"title": title, "body": body, "tags": _split_tags(tags)})
        console.print(f"Created {note['slug']}: {note['title']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("list")
def list_notes(tag: str | None = typer.Option(None, "--tag"), q: str | None = typer.Option(None, "--q"), archived: bool = typer.Option(False, "--archived")):
    params = {"include_archived": archived}
    if tag:
        params["tag"] = tag
    if q:
        params["q"] = q
    try:
        notes = client.request("GET", "/notes", params=params)
        table = Table(title="Notes")
        for col in ["slug", "title", "tags", "archived_at"]:
            table.add_column(col)
        for note in notes:
            table.add_row(note["slug"], note["title"], ", ".join(note.get("tags") or []), str(note.get("archived_at") or ""))
        console.print(table)
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("get")
def get(slug: str):
    try:
        note = client.request("GET", f"/notes/{slug}")
        console.print(f"[bold]{note['slug']} — {note['title']}[/bold]\n{note['body']}\n\nTags: {', '.join(note.get('tags') or [])}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)


@app.command("archive")
def archive(slug: str):
    try:
        note = client.request("POST", f"/notes/{slug}/archive")
        console.print(f"Archived {note['slug']}")
    except APIError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
