import typer

from .commands import epic, issue, note, project, runbook, task

app = typer.Typer(help="work-manager CLI")
app.add_typer(task.app, name="task")
app.add_typer(note.app, name="note")
app.add_typer(issue.app, name="issue")
app.add_typer(runbook.app, name="runbook")
app.add_typer(project.app, name="project")
app.add_typer(epic.app, name="epic")

if __name__ == "__main__":
    app()
