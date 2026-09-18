# 0003 — Read a document's `Status:` header; drop superseded documents from `search` by default

**Status:** accepted · **Date:** 2026-09-17

## Context

`docs/decisions/` records carry a `**Status:** accepted · **Date:** …` header, and a changed
decision is recorded as a new file with the old one marked `superseded by NNNN`. Embedding search
scores a superseded decision and its replacement identically for the same query, so an agent got
both at equal confidence and had to open each to find out which was current. The status line only
appeared in the excerpt when the first chunk happened to be the hit.

## Decision

- `index` reads the first `Status:` line in a document's first 20 lines (`**Status:** x`,
  `Status: x`, frontmatter `status: x`; only the first ` · `-separated field; values over 40 chars
  are project-status prose and ignored) and stores it on the `documents` row.
- `search` prints it on the hit line as `[status]` and drops documents whose status starts with
  `superseded` unless `--include-superseded` is passed. Mirrors the `archive/` exclusion of
  [0002](0002-content-dedup-and-archive-exclusion.md): retired material is reachable on request,
  never by accident.
- `find` is untouched.

Also done while here: a sweep at the end of `index` deletes chunks whose hash no document
references, and `search` filters those out defensively. Eleven such orphans were in the live
index and one ranked on a real query, crashing `search` with no path to print.

## Consequences

- One `ALTER TABLE` migration; every existing row is re-read once (size zeroed to defeat the
  mtime fast path) but nothing is re-embedded.
- Status is a document property, and content dedup means identical bytes share a header, so the
  hash-level lookup at search time is exact.
- Statuses seen after the first run over the workspace: `approved` 8, `accepted` 3, `design` 2,
  `active`, `planning` 1 each. The vocabulary is not enforced; only the `superseded` prefix has
  behaviour.
