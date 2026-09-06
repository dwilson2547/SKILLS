---
name: doc-indexer
description: 'Search every markdown file in the workspace superrepo — issues, decisions, notes, topics, READMEs — across all domains and submodules, semantically or by literal text. Use BEFORE non-trivial work to check whether a problem was already solved, a decision already made, or a gotcha already recorded, and whenever looking for something whose location is unknown. Trigger phrases: search the docs, check the notes, have we hit this before, did we solve this already, is there documentation for X, what do we know about X, prior art, known issues, past decisions, find where X is mentioned, look it up in the workspace. Also run index after writing or moving markdown so retrieval stays current.'
---

# doc-indexer

One local index over every markdown file in the workspace superrepo. This is the **single point of
access** to workspace knowledge — it replaced five separate services (`ai-notes-server`,
`context-store`, `tool-docs`, `todo-store`, `workman`), all abandoned because the sprawl cost more
than it returned. Do not reach for those; do not build another one.

Local SQLite, no server, no daemon, no network.

## When to use it

**Before non-trivial work**, per `CONVENTIONS.md` §5's recall rule: search first to find out whether
this problem already has a recorded answer. Skip the lookup for trivial or cosmetic work — renames,
formatting, one-line fixes — where not searching is the correct default.

Also whenever you need something and don't know where it lives. The whole point is that you should
not have to know which domain or submodule a fact was filed under.

## Commands

Three, deliberately. Resist adding a fourth.

```bash
doc-indexer search "<natural language question>"   # semantic — concepts, symptoms, "how do we…"
doc-indexer find "<exact text>"                    # literal — symbols, error strings, config keys
doc-indexer index <base-dir>                       # refresh; incremental, ~1s when nothing changed
```

**`search` vs `find`:** use `search` when you know the *idea* but not the wording — a symptom, a
concept, a question. Use `find` when you know the *exact string* — a function name, an error
message, a flag. `find` needs no embeddings and is unaffected by deduplication, so it reports every
path a string appears at.

**They scope differently, and this matters when working outside the workspace.** `search` queries
the index, whose paths are absolute — it returns workspace results from *any* working directory.
`find` greps the live filesystem, defaulting to the nearest `CONVENTIONS.md` root and falling back
to the current directory. So running `find` from an unrelated project silently returns nothing
rather than searching the workspace. From outside the tree, point it explicitly:

```bash
doc-indexer find "<text>" --dir /home/daniel/documents/workspace
```

## Reading results

Every result carries its **document path**, which is how you judge relevance — the tree is scoped by
domain (§5), so `robotics/docs/notes/…` and `automotive/gyopart/docs/decisions/…` tell you what a
hit is about before you open it. Prefer opening the path over trusting the excerpt.

`search` shows one row per distinct content. `(+N identical copies)` means the same file exists at
N other paths; the one shown is canonical.

A top-level `archive/` is **excluded by default** — it holds superseded material (§4). Pass
`--include-archive` only when deliberately digging through dead history.

## Keeping it current

```bash
doc-indexer index /home/daniel/documents/workspace
```

Incremental by construction: mtime+size checked first, sha256 only if those changed, re-chunk and
re-embed only on a genuine content change. A no-op run is about a second, so run it after writing,
moving, or deleting markdown rather than letting the index drift.

## Relationship to wsnote

`meta/bin/wsnote` **writes** notes and enforces where they land. `doc-indexer` **reads** everything,
notes included, so you never need to know where something was filed. Writing a note does not make it
retrievable until the index is refreshed.

## Setup

`find` and `index --no-embed` are pure stdlib. Semantic `search` needs the embedding backend:

```bash
./install-embeddings.sh
```

The script re-execs itself into the sibling `.venv` automatically — no activation step. Without it,
`index` still records documents and `find` still works; `search` explains why it can't run.

Full detail, storage locations, and the model-choice rationale: [README.md](./README.md) and
[docs/decisions/](./docs/decisions/).
