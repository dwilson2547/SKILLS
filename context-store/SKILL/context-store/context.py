#!/usr/bin/env python3
"""context - CLI for Context Store"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = os.environ.get("CONTEXT_STORE_API_URL", "http://localhost:8001")


def api(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode() if data is not None else None
    headers = {"Content-Type": "application/json"} if body else {}
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        print(f"Error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Cannot reach context-store server at {BASE_URL}: {e.reason}", file=sys.stderr)
        sys.exit(1)


def encode_slug(slug):
    return "/".join(urllib.parse.quote(s, safe="") for s in slug.split("/"))


def fmt_doc(doc):
    tags = doc.get("tags") or ""
    lines = [f"{doc['slug']} — {doc.get('title', '')}"]
    if doc.get("description"):
        lines.append(f"  {doc['description']}")
    if tags:
        lines.append(f"  tags: {tags}")
    if doc.get("status") == "stale":
        lines.append("  [STALE]")
    return "\n".join(lines)


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_ingest(args):
    content = args.file.read()
    data = {
        "slug": args.slug,
        "content": content,
    }
    if args.title:
        data["title"] = args.title
    if args.description:
        data["description"] = args.description
    if args.tags:
        data["tags"] = args.tags
    if args.session:
        data["session_id"] = args.session
    if args.supersedes:
        data["supersedes"] = args.supersedes
    doc = api("POST", "/context", data)
    print(f"Ingested: {doc['slug']}")


def cmd_update(args):
    data = {"content": args.file.read()}
    if args.title:
        data["title"] = args.title
    if args.description:
        data["description"] = args.description
    if args.tags:
        data["tags"] = args.tags
    doc = api("PUT", f"/context/{encode_slug(args.slug)}", data)
    print(f"Updated: {doc['slug']}")


def cmd_ls(args):
    params = []
    if args.scope:
        params.append(f"scope={urllib.parse.quote(args.scope)}")
    if args.status:
        params.append(f"status={args.status}")
    if args.tags:
        params.append(f"tags={urllib.parse.quote(args.tags)}")
    qs = ("?" + "&".join(params)) if params else ""
    docs = api("GET", f"/context{qs}")
    if not docs:
        print("No context documents found.")
        return
    for doc in docs:
        print(fmt_doc(doc))
        print()


def cmd_toc(args):
    data = api("GET", f"/context/{encode_slug(args.slug)}/toc")
    print(f"{data['slug']} — {data.get('title', '')}")
    if data.get("description"):
        print(f"  {data['description']}")
    print()
    for s in data.get("sections", []):
        indent = "  " * (s["level"] - 1)
        print(f"{indent}{'#' * s['level']} {s['heading']}")
        print(f"{indent}  {s['slug']}")


def cmd_get(args):
    ref = args.ref
    if "#" in ref:
        slug, h_slug = ref.split("#", 1)
        sec = api("GET", f"/context/{encode_slug(slug)}/sections/{urllib.parse.quote(h_slug, safe='')}")
        if sec.get("heading"):
            print(f"{'#' * sec['level']} {sec['heading']}")
            print()
        print(sec["content"])
    else:
        doc = api("GET", f"/context/{encode_slug(ref)}")
        print(f"# {doc.get('title', doc['slug'])}")
        print(f"slug: {doc['slug']}")
        if doc.get("description"):
            print(f"description: {doc['description']}")
        print()
        print(doc["content"])


def cmd_search(args):
    data = {"query": args.query, "limit": args.limit}
    if args.scope:
        data["scope"] = args.scope
    results = api("POST", "/context/search", data)
    if not results:
        print("No results.")
        return
    for r in results:
        print(f"[{r['score']}] {r['document_slug']} — {r['section_heading'] or '(no heading)'}")
        print(f"  section: {r['section_slug']}")
        print(f"  {r['preview'][:150]}")
        print()


def cmd_slugs(args):
    params = []
    if args.scope:
        params.append(f"scope={urllib.parse.quote(args.scope)}")
    qs = ("?" + "&".join(params)) if params else ""
    slugs = api("GET", f"/slugs{qs}")
    for s in slugs:
        print(s)


def cmd_stale(args):
    api("PATCH", f"/context/{encode_slug(args.slug)}/status", {"status": "stale"})
    print(f"Marked stale: {args.slug}")


def cmd_activate(args):
    api("PATCH", f"/context/{encode_slug(args.slug)}/status", {"status": "active"})
    print(f"Marked active: {args.slug}")


def cmd_delete(args):
    api("DELETE", f"/context/{encode_slug(args.slug)}")
    print(f"Deleted: {args.slug}")


def cmd_children(args):
    children = api("GET", f"/context/{encode_slug(args.slug)}/children")
    if not children:
        print("No children.")
        return
    for doc in children:
        print(fmt_doc(doc))


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="context", description="Context Store CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ingest", help="Ingest a markdown file as a new context document")
    p.add_argument("file", type=argparse.FileType("r"), help="Markdown file to ingest")
    p.add_argument("--slug", required=True, help="Document slug (e.g. junkyard-scraper/auth)")
    p.add_argument("--title", help="Document title")
    p.add_argument("--description", help="One-line description")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--session", help="Session ID")
    p.add_argument("--supersedes", help="Slug of document this replaces")
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("update", help="Replace content of an existing context document")
    p.add_argument("slug")
    p.add_argument("--file", required=True, type=argparse.FileType("r"), help="New markdown file")
    p.add_argument("--title")
    p.add_argument("--description")
    p.add_argument("--tags")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("ls", help="List context documents")
    p.add_argument("--scope", help="Slug prefix filter")
    p.add_argument("--status", default="active", choices=["active", "stale", "all"])
    p.add_argument("--tags", help="Comma-separated tag filter (AND)")
    p.set_defaults(func=cmd_ls)

    p = sub.add_parser("toc", help="Show table of contents for a context document")
    p.add_argument("slug")
    p.set_defaults(func=cmd_toc)

    p = sub.add_parser("get", help="Get a context document or section (slug or slug#section)")
    p.add_argument("ref", help="slug or slug#heading-slug")
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("search", help="Semantic search across context document sections")
    p.add_argument("query")
    p.add_argument("--scope", help="Limit to slug prefix")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("slugs", help="List all slugs")
    p.add_argument("--scope", help="Slug prefix filter")
    p.set_defaults(func=cmd_slugs)

    p = sub.add_parser("stale", help="Mark a context document as stale")
    p.add_argument("slug")
    p.set_defaults(func=cmd_stale)

    p = sub.add_parser("activate", help="Mark a stale context document as active")
    p.add_argument("slug")
    p.set_defaults(func=cmd_activate)

    p = sub.add_parser("delete", help="Hard delete a context document")
    p.add_argument("slug")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("children", help="List immediate children of a slug")
    p.add_argument("slug")
    p.set_defaults(func=cmd_children)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
