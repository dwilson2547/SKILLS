---
name: ai-tool-docs
description: >
  Use when searching indexed documentation for libraries and tools not covered by Context7.
  The AI Tool Docs Server (http://localhost:8002) indexes GitHub repository docs locally
  and provides semantic search across them. Query it before guessing at API behaviour or
  configuration options for any indexed library.
  Trigger phrases: tool docs, check the docs, look up documentation, indexed docs.
applyTo: "**"
---

# AI Tool Docs Server

A local documentation index. Pull markdown docs from GitHub repositories, index them
with semantic embeddings, and query them without leaving your context window.

> If `docs` is not installed, follow [INSTALL.md](./INSTALL.md). If the CLI is unusable,
> see [FALLBACK.md](./FALLBACK.md) for curl commands.

---

## When to Use

**Before guessing at API behaviour** — search the docs first.

**When Context7 doesn't cover a library** — check here before falling back to general knowledge.

**When you need exact configuration syntax** — docs are indexed verbatim, no hallucination risk.

**Do not use** — for libraries already in Context7 (kubernetes, docker, helm, argocd, etc.).

---

## CLI Usage

```bash
# Always start here — semantic search across all indexed docs
docs search "how to configure rate limiting"
docs search "authentication token setup" --limit 10
docs search "connection pool options" --source my-library

# Inspect what's indexed
docs sources                              # list all sources
docs source 3                             # show source detail

# Manage sources (also available in the UI at http://localhost:3002)
docs add "my-library" --repo owner/repo --branch main --folders docs
docs add "ghz" --repo bojand/ghz --folders docs --glob "*.md"
docs sync 1                               # force re-index source id 1
docs delete 3                             # remove source and all its sections
```

---

## Interpreting Results

- Results are ranked by **cosine similarity** — higher score = more relevant.
- Each result shows the **file path**, **heading**, **source name**, and a content snippet.
- If a result is truncated, use `docs get <id>` to view the full section.

---

## Note Quality

After finding something useful, save a pointer to the notes server:

```bash
notes add "ghz load test flags" "Use --rps for rate, --duration for time, --concurrency for workers. See ghz docs source id 2." --tags ghz,load-testing
```
