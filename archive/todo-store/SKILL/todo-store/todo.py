#!/usr/bin/env python3
"""todo - CLI for Todo Store"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("TODO_STORE_API_URL", "http://localhost:8003")


def api(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        print(f"Error {exc.code}: {exc.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as exc:
        print(f"Cannot reach todo-store at {BASE_URL}: {exc.reason}", file=sys.stderr)
        sys.exit(1)


def _fmt_todo(todo):
    lines = [f"[{todo['id']}] {todo['title']}"]
    lines.append(f"  status: {todo['status']} | priority: {todo['priority']}")
    if todo.get("tags"):
        lines.append(f"  tags: {todo['tags']}")
    if todo.get("description"):
        lines.append(f"  desc: {todo['description']}")
    if todo.get("completed_at"):
        lines.append(f"  completed_at: {todo['completed_at']}")
    if todo.get("completion_description"):
        lines.append(f"  completion: {todo['completion_description']}")
    return "\n".join(lines)


def cmd_ls(args):
    params = []
    if args.status:
        params.append(f"status={urllib.parse.quote(args.status)}")
    if args.priority:
        params.append(f"priority={urllib.parse.quote(args.priority)}")
    if args.tags:
        params.append(f"tags={urllib.parse.quote(args.tags)}")
    if args.query:
        params.append(f"q={urllib.parse.quote(args.query)}")
    qs = ("?" + "&".join(params)) if params else ""
    todos = api("GET", f"/todos{qs}")
    if not todos:
        print("No todos found.")
        return
    for todo in todos:
        print(_fmt_todo(todo))
        print()


def cmd_add(args):
    payload = {
        "title": args.title,
        "description": args.description,
        "tags": args.tags,
        "priority": args.priority,
        "status": args.status,
    }
    todo = api("POST", "/todos", payload)
    print(f"Created todo {todo['id']}: {todo['title']}")


def cmd_get(args):
    todo = api("GET", f"/todos/{args.todo_id}")
    print(_fmt_todo(todo))


def cmd_update(args):
    payload = {}
    if args.title is not None:
        payload["title"] = args.title
    if args.description is not None:
        payload["description"] = args.description
    if args.tags is not None:
        payload["tags"] = args.tags
    if args.priority is not None:
        payload["priority"] = args.priority
    if args.status is not None:
        payload["status"] = args.status
    if args.note is not None:
        payload["completion_description"] = args.note

    todo = api("PUT", f"/todos/{args.todo_id}", payload)
    print(f"Updated todo {todo['id']}: {todo['title']}")


def cmd_done(args):
    payload = {}
    if args.note is not None:
        payload["completion_description"] = args.note
    todo = api("PATCH", f"/todos/{args.todo_id}/complete", payload)
    print(f"Completed todo {todo['id']}: {todo['title']}")


def cmd_reopen(args):
    todo = api("PUT", f"/todos/{args.todo_id}", {"status": "open"})
    print(f"Reopened todo {todo['id']}: {todo['title']}")


def cmd_delete(args):
    api("DELETE", f"/todos/{args.todo_id}")
    print(f"Deleted todo {args.todo_id}")


def cmd_export(args):
    payload = api("GET", "/todos/export")
    with open(args.path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
    print(f"Exported todos to {args.path}")


def cmd_import(args):
    with open(args.path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if "todos" not in payload:
        print("Import file must contain a top-level 'todos' array.", file=sys.stderr)
        sys.exit(1)
    payload["mode"] = args.mode
    result = api("POST", "/todos/import", payload)
    print(
        f"Imported {result['imported']} todos "
        f"(created={result['created']}, updated={result['updated']}, replaced={result['replaced']})"
    )


def main():
    parser = argparse.ArgumentParser(prog="todo", description="Todo Store CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ls", help="List todos")
    p.add_argument("--status", default="all", choices=["all", "open", "in_progress", "blocked", "done"])
    p.add_argument("--priority", default="all", choices=["all", "low", "medium", "high", "urgent"])
    p.add_argument("--tags", help="Comma-separated tag filter (AND)")
    p.add_argument("--query", help="Substring search across title, description, and tags")
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("add", help="Create a todo")
    p.add_argument("title")
    p.add_argument("--description")
    p.add_argument("--tags")
    p.add_argument("--priority", default="medium", choices=["low", "medium", "high", "urgent"])
    p.add_argument("--status", default="open", choices=["open", "in_progress", "blocked", "done"])
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("get", help="Get one todo")
    p.add_argument("todo_id", type=int)
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("update", help="Update a todo")
    p.add_argument("todo_id", type=int)
    p.add_argument("--title")
    p.add_argument("--description")
    p.add_argument("--tags")
    p.add_argument("--priority", choices=["low", "medium", "high", "urgent"])
    p.add_argument("--status", choices=["open", "in_progress", "blocked", "done"])
    p.add_argument("--note", help="Completion description when adjusting a done todo")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("done", help="Mark a todo done")
    p.add_argument("todo_id", type=int)
    p.add_argument("--note", help="Optional completion description")
    p.set_defaults(func=cmd_done)

    p = sub.add_parser("reopen", help="Reopen a done todo")
    p.add_argument("todo_id", type=int)
    p.set_defaults(func=cmd_reopen)

    p = sub.add_parser("delete", help="Delete a todo")
    p.add_argument("todo_id", type=int)
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("export", help="Export todos to a JSON file")
    p.add_argument("path")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("import", help="Import todos from a JSON file")
    p.add_argument("path")
    p.add_argument("--mode", default="merge", choices=["merge", "replace"])
    p.set_defaults(func=cmd_import)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
