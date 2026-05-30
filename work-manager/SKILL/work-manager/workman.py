#!/usr/bin/env python3
"""workman - CLI for Work Manager"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("WORKMAN_API_URL", "http://localhost:8010")


def api(method, path, data=None, params=None, raw_text=False):
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            if not raw:
                return None
            if raw_text:
                return raw.decode()
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return raw.decode()
    except urllib.error.HTTPError as exc:
        msg = exc.read().decode()
        try:
            detail = json.loads(msg).get("detail", msg)
        except Exception:
            detail = msg
        print(f"Error {exc.code}: {detail}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Cannot reach work-manager at {BASE_URL}: {exc.reason}", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────────────────────
# Formatters
# ─────────────────────────────────────────────────────────────

def _fmt_task(t):
    lines = [f"[{t['slug']}] {t['title']}"]
    lines.append(f"  status: {t['status']}  effort: {t.get('estimated_effort') or '-'}  assignee: {t.get('assignee') or '-'}")
    lines.append(f"  epic: {t.get('epic_slug') or '-'}  project: {t.get('project_slug') or '-'}")
    if t.get("description"):
        lines.append(f"  desc: {t['description']}")
    return "\n".join(lines)


def _fmt_criterion(c):
    check = "✓" if c["verified"] else "○"
    return f"  [{c['id']}] {check} {c['description']}"


def _fmt_testing_layer(t):
    return f"  [{t['id']}] [{t['layer']}] [{t['status']}] {t['description']}"


def _fmt_note(n):
    tags = ", ".join(n.get("tags") or [])
    lines = [f"[{n['slug']}] {n['title']}"]
    if tags:
        lines.append(f"  tags: {tags}")
    if n.get("body"):
        lines.append(f"  {n['body'][:200]}")
    return "\n".join(lines)


def _fmt_issue(i):
    lines = [f"[{i['slug']}] [{i['severity']}] [{i['status']}] {i['title']}"]
    if i.get("linked_task_slug"):
        lines.append(f"  task: {i['linked_task_slug']}")
    return "\n".join(lines)


def _fmt_project(p):
    lines = [f"[{p['slug']}] {p['title']}  status: {p['status']}"]
    if p.get("epics"):
        for e in p["epics"]:
            lines.append(f"  epic [{e['slug']}] {e['title']}  status: {e['status']}")
            for t in e.get("tasks", []):
                lines.append(f"    task [{t['slug']}] {t['title']}  status: {t['status']}")
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────
# Commands: brief / next
# ─────────────────────────────────────────────────────────────

def cmd_brief(args):
    markdown = api("GET", f"/briefs/task/{args.slug}/markdown", raw_text=True)
    print(markdown)


def cmd_next(args):
    params = {"project": args.project} if args.project else {}
    result = api("GET", "/tasks/next", params=params or None)
    if not result or not result.get("slug"):
        print("No task available.")
        return
    markdown = api("GET", f"/briefs/task/{result['slug']}/markdown", raw_text=True)
    print(markdown)


# ─────────────────────────────────────────────────────────────
# Commands: task
# ─────────────────────────────────────────────────────────────

def cmd_task_ls(args):
    params = {k: v for k, v in {"status": args.status, "project": args.project, "epic": args.epic}.items() if v}
    tasks = api("GET", "/tasks", params=params or None)
    if not tasks:
        print("No tasks found.")
        return
    for t in tasks:
        print(_fmt_task(t))
        print()


def cmd_task_get(args):
    t = api("GET", f"/tasks/{args.slug}")
    print(_fmt_task(t))
    criteria = api("GET", f"/tasks/{args.slug}/acceptance-criteria")
    if criteria:
        print("\nAcceptance Criteria:")
        for c in criteria:
            print(_fmt_criterion(c))
    layers = api("GET", f"/tasks/{args.slug}/testing-layers")
    if layers:
        print("\nTesting Layers:")
        for layer in layers:
            print(_fmt_testing_layer(layer))
    dod = api("GET", f"/tasks/{args.slug}/dod")
    if dod.get("dod_description"):
        print(f"\nDefinition of Done:\n  {dod['dod_description']}")


def cmd_task_update(args):
    payload = {k: v for k, v in {
        "status": args.status,
        "assignee": args.assignee,
        "estimated_effort": args.effort,
        "description": args.description,
    }.items() if v is not None}
    t = api("PATCH", f"/tasks/{args.slug}", data=payload)
    print(f"Updated {t['slug']}: status={t['status']}")


def cmd_task_done(args):
    t = api("PATCH", f"/tasks/{args.slug}", data={"status": "complete"})
    print(f"Marked complete: {t['slug']}")


def cmd_task_create(args):
    payload = {k: v for k, v in {
        "title": args.title,
        "description": args.description,
        "assignee": args.assignee,
        "estimated_effort": args.effort,
    }.items() if v is not None}
    t = api("POST", f"/epics/{args.epic}/tasks", data=payload)
    print(f"Created {t['slug']}: {t['title']}")


# ─────────────────────────────────────────────────────────────
# Commands: criterion
# ─────────────────────────────────────────────────────────────

def cmd_criterion_ls(args):
    items = api("GET", f"/tasks/{args.slug}/acceptance-criteria")
    if not items:
        print("No acceptance criteria.")
        return
    for c in items:
        print(_fmt_criterion(c))


def cmd_criterion_add(args):
    item = api("POST", f"/tasks/{args.slug}/acceptance-criteria", data={"description": args.description})
    print(f"Added criterion [{item['id']}]: {item['description']}")


def cmd_criterion_check(args):
    item = api("PATCH", f"/tasks/{args.slug}/acceptance-criteria/{args.criterion_id}", data={"verified": True})
    print(f"Verified criterion [{item['id']}]: {item['description']}")


def cmd_criterion_uncheck(args):
    item = api("PATCH", f"/tasks/{args.slug}/acceptance-criteria/{args.criterion_id}", data={"verified": False})
    print(f"Unverified criterion [{item['id']}]: {item['description']}")


# ─────────────────────────────────────────────────────────────
# Commands: testing
# ─────────────────────────────────────────────────────────────

def cmd_testing_ls(args):
    layers = api("GET", f"/tasks/{args.slug}/testing-layers")
    if not layers:
        print("No testing layers.")
        return
    for layer in layers:
        print(_fmt_testing_layer(layer))


def cmd_testing_add(args):
    layer = api("POST", f"/tasks/{args.slug}/testing-layers", data={"layer": args.layer_type, "description": args.description})
    print(f"Added testing layer [{layer['id']}] [{layer['layer']}]: {layer['description']}")


def cmd_testing_update(args):
    layer = api("PATCH", f"/tasks/{args.slug}/testing-layers/{args.layer_id}", data={"status": args.status})
    print(f"Updated testing layer [{layer['id']}]: status={layer['status']}")


# ─────────────────────────────────────────────────────────────
# Commands: dod
# ─────────────────────────────────────────────────────────────

def cmd_dod_get(args):
    dod = api("GET", f"/tasks/{args.slug}/dod")
    if dod.get("dod_description"):
        print(dod["dod_description"])
    else:
        print("No definition of done set.")


def cmd_dod_set(args):
    dod = api("PATCH", f"/tasks/{args.slug}/dod", data={"dod_description": args.description})
    print(f"DoD updated for {args.slug}.")


# ─────────────────────────────────────────────────────────────
# Commands: note
# ─────────────────────────────────────────────────────────────

def cmd_note_ls(args):
    params = {k: v for k, v in {"q": args.query, "tag": args.tag, "mode": args.mode}.items() if v}
    notes = api("GET", "/notes", params=params or None)
    if not notes:
        print("No notes found.")
        return
    for n in notes:
        print(_fmt_note(n))
        print()


def cmd_note_get(args):
    n = api("GET", f"/notes/{args.slug}")
    print(f"[{n['slug']}] {n['title']}")
    tags = ", ".join(n.get("tags") or [])
    if tags:
        print(f"tags: {tags}")
    print()
    print(n.get("body") or "")


def cmd_note_add(args):
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    n = api("POST", "/notes", data={"title": args.title, "body": args.body, "tags": tags})
    print(f"Created {n['slug']}: {n['title']}")


def cmd_note_archive(args):
    api("POST", f"/notes/{args.slug}/archive")
    print(f"Archived {args.slug}.")


# ─────────────────────────────────────────────────────────────
# Commands: issue
# ─────────────────────────────────────────────────────────────

def cmd_issue_ls(args):
    params = {k: v for k, v in {"status": args.status, "severity": args.severity}.items() if v}
    issues = api("GET", "/issues", params=params or None)
    if not issues:
        print("No issues found.")
        return
    for i in issues:
        print(_fmt_issue(i))
        print()


def cmd_issue_get(args):
    i = api("GET", f"/issues/{args.slug}")
    print(f"[{i['slug']}] [{i['severity']}] [{i['status']}] {i['title']}")
    for field in ("triage_steps", "root_cause", "resolution", "lessons_learned"):
        if i.get(field):
            print(f"\n{field.replace('_', ' ').title()}:\n  {i[field]}")


def cmd_issue_add(args):
    payload = {k: v for k, v in {
        "title": args.title,
        "severity": args.severity,
        "task_slug": args.task,
        "triage_steps": args.triage,
        "root_cause": args.root_cause,
        "resolution": args.resolution,
        "lessons_learned": args.lessons,
    }.items() if v is not None}
    i = api("POST", "/issues", data=payload)
    print(f"Created {i['slug']}: {i['title']}")


def cmd_issue_resolve(args):
    payload = {"status": "resolved", "resolution": args.resolution}
    i = api("PATCH", f"/issues/{args.slug}", data=payload)
    print(f"Resolved {i['slug']}.")


# ─────────────────────────────────────────────────────────────
# Commands: project tree
# ─────────────────────────────────────────────────────────────

def cmd_projects(args):
    projects = api("GET", "/projects")
    if not projects:
        print("No projects.")
        return
    for p in projects:
        print(_fmt_project(p))
        print()


# ─────────────────────────────────────────────────────────────
# Commands: export / import
# ─────────────────────────────────────────────────────────────

def cmd_export(args):
    entities = ["projects", "epics", "tasks", "subtasks", "notes", "design-docs", "issues", "runbooks"]
    result = {}
    for entity in entities:
        result[entity] = api("GET", f"/{entity}/export")
    output = json.dumps(result, indent=2)
    if args.file:
        with open(args.file, "w") as f:
            f.write(output)
        print(f"Exported to {args.file}")
    else:
        print(output)


def cmd_import(args):
    with open(args.file) as f:
        data = json.load(f)
    mode = args.mode
    entities = ["projects", "epics", "tasks", "subtasks", "notes", "design-docs", "issues", "runbooks"]
    for entity in entities:
        if entity in data:
            result = api("POST", f"/{entity}/import", data={"data": data[entity], "mode": mode})
            count = result.get("imported", "?")
            print(f"  {entity}: {count} imported")
    print("Import complete.")


# ─────────────────────────────────────────────────────────────
# Parser
# ─────────────────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(prog="workman", description="Work Manager CLI")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # brief
    p = sub.add_parser("brief", help="Get full markdown brief for a task")
    p.add_argument("slug", help="Task slug (TASK-001)")
    p.set_defaults(func=cmd_brief)

    # next
    p = sub.add_parser("next", help="Get brief for the next ready task")
    p.add_argument("--project", default=None, help="Filter by project slug")
    p.set_defaults(func=cmd_next)

    # projects
    p = sub.add_parser("projects", help="List projects with epic/task tree")
    p.set_defaults(func=cmd_projects)

    # task
    task_sub = sub.add_parser("task", help="Task commands").add_subparsers(dest="task_cmd", metavar="<subcommand>")

    p = task_sub.add_parser("ls", help="List tasks")
    p.add_argument("--status", default=None)
    p.add_argument("--project", default=None)
    p.add_argument("--epic", default=None)
    p.set_defaults(func=cmd_task_ls)

    p = task_sub.add_parser("get", help="Get task detail with criteria/testing/DoD")
    p.add_argument("slug")
    p.set_defaults(func=cmd_task_get)

    p = task_sub.add_parser("update", help="Update task fields")
    p.add_argument("slug")
    p.add_argument("--status", default=None)
    p.add_argument("--assignee", default=None)
    p.add_argument("--effort", default=None, choices=["xs", "s", "m", "l", "xl"])
    p.add_argument("--description", default=None)
    p.set_defaults(func=cmd_task_update)

    p = task_sub.add_parser("done", help="Mark task complete")
    p.add_argument("slug")
    p.set_defaults(func=cmd_task_done)

    p = task_sub.add_parser("create", help="Create a new task")
    p.add_argument("--epic", required=True, help="Epic slug")
    p.add_argument("--title", required=True)
    p.add_argument("--description", default=None)
    p.add_argument("--assignee", default=None)
    p.add_argument("--effort", default=None, choices=["xs", "s", "m", "l", "xl"])
    p.set_defaults(func=cmd_task_create)

    # criterion
    crit_sub = sub.add_parser("criterion", help="Acceptance criteria commands").add_subparsers(dest="crit_cmd", metavar="<subcommand>")

    p = crit_sub.add_parser("ls", help="List acceptance criteria for a task")
    p.add_argument("slug", help="Task slug")
    p.set_defaults(func=cmd_criterion_ls)

    p = crit_sub.add_parser("add", help="Add acceptance criterion to a task")
    p.add_argument("slug", help="Task slug")
    p.add_argument("description", help="Criterion description")
    p.set_defaults(func=cmd_criterion_add)

    p = crit_sub.add_parser("check", help="Mark criterion as verified")
    p.add_argument("slug", help="Task slug")
    p.add_argument("criterion_id", type=int, help="Criterion ID")
    p.set_defaults(func=cmd_criterion_check)

    p = crit_sub.add_parser("uncheck", help="Mark criterion as not verified")
    p.add_argument("slug", help="Task slug")
    p.add_argument("criterion_id", type=int, help="Criterion ID")
    p.set_defaults(func=cmd_criterion_uncheck)

    # testing
    test_sub = sub.add_parser("testing", help="Testing layer commands").add_subparsers(dest="test_cmd", metavar="<subcommand>")

    p = test_sub.add_parser("ls", help="List testing layers for a task")
    p.add_argument("slug", help="Task slug")
    p.set_defaults(func=cmd_testing_ls)

    p = test_sub.add_parser("add", help="Add a testing layer to a task")
    p.add_argument("slug", help="Task slug")
    p.add_argument("layer_type", choices=["unit", "integration", "e2e", "manual", "observability"])
    p.add_argument("description")
    p.set_defaults(func=cmd_testing_add)

    p = test_sub.add_parser("update", help="Update testing layer status")
    p.add_argument("slug", help="Task slug")
    p.add_argument("layer_id", type=int)
    p.add_argument("--status", required=True, choices=["pending", "passed", "failed", "skipped"])
    p.set_defaults(func=cmd_testing_update)

    # dod
    dod_sub = sub.add_parser("dod", help="Definition of done commands").add_subparsers(dest="dod_cmd", metavar="<subcommand>")

    p = dod_sub.add_parser("get", help="Get definition of done for a task")
    p.add_argument("slug", help="Task slug")
    p.set_defaults(func=cmd_dod_get)

    p = dod_sub.add_parser("set", help="Set definition of done for a task")
    p.add_argument("slug", help="Task slug")
    p.add_argument("description", help="DoD description text")
    p.set_defaults(func=cmd_dod_set)

    # note
    note_sub = sub.add_parser("note", help="Note commands").add_subparsers(dest="note_cmd", metavar="<subcommand>")

    p = note_sub.add_parser("ls", help="List/search notes")
    p.add_argument("--query", default=None, help="Text or semantic query")
    p.add_argument("--tag", default=None, help="Filter by tag")
    p.add_argument("--mode", default=None, choices=["text", "semantic"], help="Search mode")
    p.set_defaults(func=cmd_note_ls)

    p = note_sub.add_parser("get", help="Get a note by slug")
    p.add_argument("slug")
    p.set_defaults(func=cmd_note_get)

    p = note_sub.add_parser("add", help="Add a note")
    p.add_argument("title")
    p.add_argument("body")
    p.add_argument("--tags", default=None, help="Comma-separated tags (at least one must start with scope:)")
    p.set_defaults(func=cmd_note_add)

    p = note_sub.add_parser("archive", help="Archive a note")
    p.add_argument("slug")
    p.set_defaults(func=cmd_note_archive)

    # issue
    issue_sub = sub.add_parser("issue", help="Issue commands").add_subparsers(dest="issue_cmd", metavar="<subcommand>")

    p = issue_sub.add_parser("ls", help="List issues")
    p.add_argument("--status", default=None, choices=["open", "resolved"])
    p.add_argument("--severity", default=None, choices=["sev1", "sev2", "sev3"])
    p.set_defaults(func=cmd_issue_ls)

    p = issue_sub.add_parser("get", help="Get issue detail")
    p.add_argument("slug")
    p.set_defaults(func=cmd_issue_get)

    p = issue_sub.add_parser("add", help="File a new issue")
    p.add_argument("title")
    p.add_argument("--task", default=None, help="Linked task slug")
    p.add_argument("--severity", default="sev2", choices=["sev1", "sev2", "sev3"])
    p.add_argument("--triage", default=None, dest="triage", help="Triage steps")
    p.add_argument("--root-cause", default=None, dest="root_cause")
    p.add_argument("--resolution", default=None)
    p.add_argument("--lessons", default=None, dest="lessons")
    p.set_defaults(func=cmd_issue_add)

    p = issue_sub.add_parser("resolve", help="Mark an issue resolved")
    p.add_argument("slug")
    p.add_argument("--resolution", default=None)
    p.set_defaults(func=cmd_issue_resolve)

    # export / import
    p = sub.add_parser("export", help="Export all data to JSON")
    p.add_argument("file", nargs="?", default=None, help="Output file (default: stdout)")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="Import data from JSON export")
    p.add_argument("file", help="Input JSON file")
    p.add_argument("--mode", default="merge", choices=["merge", "replace"])
    p.set_defaults(func=cmd_import)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
