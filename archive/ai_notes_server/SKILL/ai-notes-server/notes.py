#!/usr/bin/env python3
"""notes - CLI for AI Notes Server"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("NOTES_API_URL", "http://localhost:8000")


def api(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Cannot reach notes server at {BASE_URL}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fmt_note(note):
    tags = " ".join(f"#{t}" for t in note.get("tags", []))
    parts = [f"[{note['id']}] {note['title']}"]
    if tags:
        parts.append(f"  {tags}")
    parts.append(f"  {note['content']}")
    return "\n".join(parts)


def cmd_search(args):
    q = urllib.parse.quote(args.query)
    results = api("GET", f"/notes/search?q={q}&limit={args.limit}")
    if not results:
        print("No results.")
        return
    for item in results:
        print(fmt_note(item["note"]))
        print()


def cmd_add(args):
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else []
    note = api("POST", "/notes", {"title": args.title, "content": args.content, "tags": tags})
    print(f"Created note {note['id']}")


def cmd_update(args):
    data = {}
    if args.title:
        data["title"] = args.title
    if args.content:
        data["content"] = args.content
    if args.tags is not None:
        data["tags"] = [t.strip() for t in args.tags.split(",")]
    if not data:
        print("Nothing to update.", file=sys.stderr)
        sys.exit(1)
    note = api("PUT", f"/notes/{args.id}", data)
    print(f"Updated note {note['id']}")


def cmd_get(args):
    note = api("GET", f"/notes/{args.id}")
    print(fmt_note(note))


def cmd_archive(args):
    note = api("POST", f"/notes/{args.id}/archive")
    status = "Archived" if note.get("archived_at") else "Unarchived"
    print(f"{status} note {note['id']}")


def main():
    parser = argparse.ArgumentParser(prog="notes", description="AI Notes Server CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("search", help="Semantic search notes")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("add", help="Create a note")
    p.add_argument("title")
    p.add_argument("content")
    p.add_argument("--tags", help="Comma-separated tags")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("update", help="Update a note")
    p.add_argument("id", type=int)
    p.add_argument("--title")
    p.add_argument("--content")
    p.add_argument("--tags", help="Comma-separated tags (replaces existing)")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("get", help="Get a note by ID")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("archive", help="Toggle archive on a note")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_archive)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
