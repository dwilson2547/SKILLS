# Decision: dedup embeddings by content hash; exclude top-level `archive/` by default

**Date:** 2026-09-06

## Context

A corpus measurement after the initial build found ~41% of indexed documents (972 of 2,347) lived
under `archive/` — per `CONVENTIONS.md` §4, "superseded / dead, kept for history only" — and that
970 of 2,347 documents (across the whole corpus, archive and live) were byte-identical redundant
copies of only 394 distinct hashes. Worst case: a boilerplate stub README with 96 identical copies
across `ai/ai-projects/*`. This wasn't hypothetical: real queries surfaced the *same* file at
multiple paths and identical scores in the top results, crowding out genuinely distinct matches
(e.g. `passkey.md` occupying 3 of the top 5 slots for one query, all from `archive/wiki-demo/`'s
several forks of the same wiki export).

## Decision 1 — `index` excludes a top-level `archive/` by default

Scoped strictly to a directory literally named `archive` sitting directly under the indexed
`base-dir` — not any directory named "archive" anywhere in the tree, since a project may
legitimately have its own nested archive folder. `--include-archive` opts back in.

`find` is untouched: it never consults the index or this exclusion, so a literal string still
finds every occurrence including in `archive/`. This is a `search`-relevance decision, not a
"pretend archive/ doesn't exist" decision.

## Decision 2 — chunks are keyed by content hash, not path

Every document's path, size, mtime, hash, and title are still recorded individually in
`documents` — nothing is dropped, so `find`'s live grep (which doesn't touch the DB at all) and
any per-path metadata lookup are unaffected. But `chunks` (the table that holds chunk text and
embeddings) is now keyed by `content_hash`, not by path. Chunking and embedding happen once per
distinct hash; every document whose content matches that hash shares those rows.

Consequences:
- Cold-index cost drops roughly in proportion to the duplication rate, since embedding is the
  expensive step. Measured: 17,611 chunks → 8,947 chunks after dedup (was already also dropping
  archive/, so this reflects both changes together — see numbers in README).
- Deleting or changing a document only deletes its hash's chunks when no other document still
  references that hash (`_hash_orphaned` in the script) — a shared hash isn't destroyed out from
  under a sibling duplicate that's still on disk.
- `search` groups by `content_hash`: one ranked result per distinct content, showing a
  deterministic canonical path (alphabetically first among duplicates, preferring one inside a
  `--dir` filter if given) plus a `(+N identical copies)` note when duplicates exist. No path ever
  occupies two ranked slots for the same content.

## Migration

This changed the `chunks` table's primary key shape (`doc_path` → `content_hash`), which isn't a
row-level migration worth writing — `doc-indexer` detects the old schema (`_migrate_if_needed`)
and rebuilds `chunks`/`documents` from scratch, followed by a one-time `VACUUM` to reclaim the
dropped tables' pages (skipping the VACUUM left the file at its old high-water-mark size even
though row count had roughly halved — caught by comparing before/after `du -h` during
verification, not by inspection). The next `index` run repopulates everything; this is a local
cache, not a system of record, so a one-time full re-embed is an acceptable cost for a schema
change.
