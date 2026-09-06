#!/usr/bin/env python3
"""docs - CLI for AI Tool Docs Server"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("DOCS_API_URL", "http://localhost:8002")


def api(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(
            f"Cannot reach docs server at {BASE_URL}: {e.reason}\n"
            "Is the service running? See INSTALL.md or FALLBACK.md.",
            file=sys.stderr,
        )
        sys.exit(1)


def fmt_section(sec, source_name=None, score=None):
    lines = []
    heading = sec.get("heading") or "(document root)"
    lines.append(f"[{sec['id']}] {heading}  ({sec['file_path']})")
    if source_name:
        lines.append(f"  source: {source_name}")
    if score is not None:
        lines.append(f"  score:  {score:.1%}")
    content = sec.get("content", "")
    preview = content[:300] + ("…" if len(content) > 300 else "")
    lines.append(f"  {preview}")
    return "\n".join(lines)


def fmt_source(s):
    folders = ", ".join(s.get("docs_folders") or []) or "(whole repo)"
    synced = s.get("last_synced_at") or "never"
    return (
        f"[{s['id']}] {s['name']}  ({s['repo']}@{s['branch']})\n"
        f"  status: {s['status']}  sections: {s.get('section_count', 0)}\n"
        f"  folders: {folders}  glob: {s.get('file_glob','*.md')}\n"
        f"  last sync: {synced}"
    )


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_search(args):
    params = urllib.parse.urlencode({
        "q": args.query,
        "limit": args.limit,
        **({"source_id": args.source} if args.source else {}),
    })
    results = api("GET", f"/docs/search?{params}")
    if not results:
        print("No results.")
        return
    for item in results:
        print(fmt_section(item["section"], item.get("source_name"), item.get("score")))
        print()


def cmd_get(args):
    sec = api("GET", f"/docs/{args.id}")
    print(fmt_section(sec))
    print()
    print(sec.get("content", ""))


def cmd_sources(args):
    sources = api("GET", "/sources")
    if not sources:
        print("No sources configured.")
        return
    for s in sources:
        print(fmt_source(s))
        print()


def cmd_source(args):
    s = api("GET", f"/sources/{args.id}")
    print(fmt_source(s))
    if s.get("error_message"):
        print(f"  error: {s['error_message']}")


def cmd_add(args):
    folders = [f.strip() for f in args.folders.split(",")] if args.folders else []
    body = {
        "name": args.name,
        "repo": args.repo,
        "branch": args.branch,
        "docs_folders": folders,
        "file_glob": args.glob,
    }
    s = api("POST", "/sources", body)
    print(f"Created source {s['id']}: {s['name']}")
    if not args.no_sync:
        api("POST", f"/sources/{s['id']}/sync")
        print(f"Sync started for source {s['id']} (runs in background)")


def cmd_sync(args):
    result = api("POST", f"/sources/{args.id}/sync")
    print(result.get("detail", "Sync started"))


def cmd_delete(args):
    api("DELETE", f"/sources/{args.id}")
    print(f"Deleted source {args.id}")


def cmd_stats(args):
    s = api("GET", "/stats")
    print(
        f"Sources: {s['source_count']}\n"
        f"Files:   {s['file_count']}\n"
        f"Sections:{s['section_count']}"
    )


def main():
    parser = argparse.ArgumentParser(
        prog="docs",
        description="AI Tool Docs Server CLI — search indexed documentation",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p = sub.add_parser("search", help="Semantic search across indexed docs")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--source", type=int, help="Filter by source id")
    p.set_defaults(func=cmd_search)

    # get
    p = sub.add_parser("get", help="Get a single doc section by id")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_get)

    # sources
    p = sub.add_parser("sources", help="List all sources")
    p.set_defaults(func=cmd_sources)

    # source
    p = sub.add_parser("source", help="Show a source by id")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_source)

    # add
    p = sub.add_parser("add", help="Add a new source")
    p.add_argument("name", help="Friendly name for the source")
    p.add_argument("--repo", required=True, help="owner/repo")
    p.add_argument("--branch", default="main")
    p.add_argument("--folders", help="Comma-separated repo-relative folders")
    p.add_argument("--glob", default="*.md", help="File glob pattern (default: *.md)")
    p.add_argument("--no-sync", action="store_true", help="Skip automatic initial sync")
    p.set_defaults(func=cmd_add)

    # sync
    p = sub.add_parser("sync", help="Trigger a sync for a source")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_sync)

    # delete
    p = sub.add_parser("delete", help="Delete a source and all its sections")
    p.add_argument("id", type=int)
    p.set_defaults(func=cmd_delete)

    # stats
    p = sub.add_parser("stats", help="Show aggregate stats")
    p.set_defaults(func=cmd_stats)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
