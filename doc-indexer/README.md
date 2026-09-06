---
tier: project
domain: meta
status: active
---

# doc-indexer

One local index over all workspace markdown, built for AI agents. This is the deliberate
replacement for five previously-abandoned knowledge services (`ai-notes-server`, `context-store`,
`tool-docs`, `todo-store`, `workman`) — their tool sprawl caused more friction than it solved.
`doc-indexer` is ONE local CLI, ONE SQLite file, three commands, no server, no daemon.

Audience is AI agents, not humans: output is terse and always includes the document path so an
agent can judge domain relevance from the path itself (see `CONVENTIONS.md` §5 — repo-local docs
are scoped structurally, by directory).

## Install

Nothing to install for `index --no-embed` and `find` — the tool is a single stdlib-only Python 3
script:

```bash
meta/SKILLS/doc-indexer/doc-indexer find "some text"
```

Semantic `search` (and embedding during `index`) needs one optional dependency, `fastembed`.
Set it up once:

```bash
meta/SKILLS/doc-indexer/install-embeddings.sh
```

This creates `meta/SKILLS/doc-indexer/.venv` and installs `fastembed` into it. `doc-indexer` detects that
venv and transparently re-execs itself into it — no `source .venv/bin/activate`, no PATH changes.
If the venv is absent, embedding-dependent operations degrade gracefully: `index` still records
every document (path, hash, chunks) and reports *why* embedding was skipped; `search` exits with a
clear one-line explanation instead of a stack trace; `find` is entirely unaffected since it never
touches the embedding path at all.

Optionally symlink it onto your `PATH` (matching `meta/bin/wsnote`'s convention):

```bash
ln -s "$(pwd)/meta/SKILLS/doc-indexer/doc-indexer" ~/.local/bin/doc-indexer
```

## Commands

Exactly three. Resist adding a fourth — that's how the five predecessor services happened.

### `doc-indexer index <base-dir>`

Recursively scans `<base-dir>` for `*.md`/`*.markdown`, skipping `.git/`, `node_modules/`,
`venv/`, `.venv/`, `__pycache__/`, `dist/`, `build/`, anything a `.gitignore` in the tree covers
(best-effort: simple name/glob patterns, not full gitignore semantics), and — by default — a
top-level `archive/` sitting directly under `<base-dir>` (`CONVENTIONS.md` §4: "superseded / dead,
kept for history only"; pass `--include-archive` to index it anyway). The archive exclusion is
scoped to that one top-level directory, not any directory named "archive" anywhere in the tree, so
a project's own nested archive folder is left alone. Each file is chunked (~1200 chars,
paragraph-aware, oversized paragraphs hard-split so one giant code block can't blow up a chunk or
an embedding batch).

**Deduplicated by content hash**: identical files are chunked and embedded exactly once. Every
path is still recorded individually in `documents` (nothing is dropped — `find` and per-path
metadata are unaffected), but `chunks` is keyed by content hash, so N byte-identical copies share
one set of chunks/embeddings instead of paying the embedding cost N times. See
`docs/decisions/0002-content-dedup-and-archive-exclusion.md` for why and the measured effect.

**Incremental by construction**: for each file, mtime+size is checked first (cheap); if either
changed, the file is re-read and sha256-hashed, and only a hash mismatch triggers re-chunking and
re-embedding. A file whose mtime changed but content didn't (e.g. `touch`) is recorded as
unchanged. Records for files no longer on disk are removed, scoped to the indexed root (indexing
one subtree never deletes records belonging to a different indexed root); a hash's chunks are only
deleted once no document anywhere still references that hash. Re-running `index` after enabling
embeddings for the first time (or after `--no-embed`) also back-fills embeddings for
already-unchanged documents that don't have one yet, or that were embedded under a different
`--model` — so turning embeddings on later doesn't require a content change to take effect.

Reports `added=N updated=N unchanged=N removed=N` (counted per path) plus how many chunks were
(or were not) embedded, across how many *distinct* documents, and why.

Flags: `--db PATH`, `--no-embed` (metadata/chunks only, no embedding attempt), `--model NAME`
(override the embedding model), `--include-archive` (don't exclude top-level `archive/`).

### `doc-indexer search <query>`

Semantic search over stored embeddings. Embeds the query (using fastembed's query-side encoding),
does a brute-force cosine scan against every stored chunk vector loaded into memory as one NumPy
matrix (see "Why brute force" below), and prints the best-scoring chunk **per distinct content
hash**, ranked — never per path, so N identical copies of a file never occupy N result slots:

```
0.674  meta/SKILLS/superpowers-review/writing-skills/anthropic-best-practices.md:1011-1024
       List required packages in your SKILL.md and verify they're available in the …
0.356  docs/wiki/core_concepts/development/security/passkey.md:66-76  (+1 identical copies)
       Device Signs Challenge: The device uses the private key to sign the challenge, proving …
```

Format: `<score>  <path>:<start_line>-<end_line>` (plus `(+N identical copies)` when the content
is duplicated elsewhere) then an indented excerpt line. The shown path is a deterministic
canonical choice (alphabetically first among duplicates; one inside `--dir` if that's given) — use
`find` if you need the full list of paths sharing that content. Flags: `--db PATH`, `-n/--top N`
(default 8), `--dir PREFIX` (restrict to a path prefix, e.g. a single domain), `--model NAME`.

If no embeddings exist yet (fastembed never installed, or `index` was run with `--no-embed`),
`search` exits immediately with the exact reason and the command to fix it — it never crashes into
a traceback.

### `doc-indexer find <text>`

Literal/exact substring search. Pure stdlib, no DB, no embeddings — it walks the directory tree
live (same skip-list/`.gitignore` handling as `index`) and greps every markdown file line by line,
so results are always current even if you haven't re-indexed. This is the fast path for "does this
exact string appear anywhere," and it's genuinely dependency-free: it works even if `doc-indexer`
has never been given a `.venv` or a DB at all.

Defaults to scanning from the nearest ancestor directory containing `CONVENTIONS.md` (i.e. the
workspace root, when run from inside it), matching `wsnote`'s convention of a structural default
scope. Override with `--dir`. Other flags: `--case-sensitive`, `--max-files N`, `--max-per-file N`
(lines shown per file, default 5).

```
$ doc-indexer find "bge-small"
meta/SKILLS/ai_notes_server/README.md
  10: - **API** — FastAPI + SQLite + [fastembed](...) (`BAAI/bge-small-en-v1.5` via ONNX — no PyTorch)
```

## Storage

SQLite, one file, two tables: `documents` (one row per path — size, mtime, hash, title) and
`chunks` (one set of rows per *distinct content hash* — text, embedding as a raw float32 BLOB).
Default location: `~/.local/share/doc-indexer/index.db`. Override with `--db PATH` or
`DOC_INDEXER_DB`. Nothing is written inside the workspace repo itself, so there's nothing to
`.gitignore` at the repo level; the `.venv` and any stray local DB *inside this project folder*
(if you ever point `--db` there) are covered by this project's own `.gitignore`.

The embedding model's ONNX weights are cached separately, under `~/.cache/doc-indexer/models` by
default (override with `DOC_INDEXER_MODEL_CACHE`) — also outside the repo.

## Embedding model: `sentence-transformers/all-MiniLM-L6-v2`

Served locally via [fastembed](https://github.com/qdrant/fastembed) (ONNX Runtime, CPU-only, no
PyTorch) — this is the only third-party dependency in the whole tool, and it's isolated behind a
lazy import so nothing else needs it.

This was **not** the first choice. fastembed's own default, `BAAI/bge-small-en-v1.5`, was tried
first — it's the same model the abandoned `ai-notes-server`/`context-store` services used, and
looked like the obvious continuation. Benchmarking on the actual target machine (AMD Ryzen 5 5600H)
found its quantized (int8) ONNX kernels running at **~480ms per chunk** — over an hour to embed the
whole workspace. Profiling pointed squarely at `onnxruntime`'s `run()` call itself (not
tokenization, not batching), consistent with known int8 quant-kernel slowness on CPUs without
VNNI/AVX-512 support. Switching to `all-MiniLM-L6-v2` — same size class (22M params, 384-dim
output, ~90MB), but fp32, not quantized — measured **~11ms per chunk**, a ~43x speedup, with no
setup difference. At that point the choice was easy: MiniLM-L6-v2 is one of the most widely used
and validated small sentence-embedding models in the ecosystem, its retrieval quality is well
within noise of bge-small for this use case (short markdown chunks, brute-force top-k, not a
leaderboard benchmark), and "fast enough that re-indexing the whole workspace takes half a minute
instead of an hour" matters far more here than a marginal MTEB score.

Both models produce L2-normalized vectors (verified empirically, not assumed), so `search`
normalizes anyway before the dot product rather than trusting that.

**Why brute-force cosine instead of a vector DB**: at workspace scale (§ below — ~1,400 live docs,
~9k distinct chunks measured after dedup), the full embedding matrix is a few tens of MB. NumPy's
`mat @ query` scans all of it in a few milliseconds. A vector index (FAISS, sqlite-vec, etc.) buys
nothing at this scale and is exactly the kind of extra moving part this tool exists to avoid.
Revisit only if the corpus grows an order of magnitude or more.

**Why fastembed and not `sentence-transformers` directly**: fastembed ships ONNX Runtime only —
no PyTorch — which is a materially smaller and faster-to-install dependency for a CLI tool that
should stay closer to `wsnote`'s zero-dependency spirit than to a full ML stack.

## Measured numbers (real workspace run)

### First build (before dedup / archive exclusion)

`doc-indexer index /home/daniel/documents/workspace`, embedding everything including `archive/`
and every duplicate copy: **2,347 documents → 17,611 chunks, 71 MB DB, 4m 9s cold index time.**
A corpus check afterward found 972 of those 2,347 documents (41%) under `archive/`, and 970 of
2,347 documents workspace-wide were byte-identical redundant copies of only 394 distinct hashes —
see `docs/decisions/0002-content-dedup-and-archive-exclusion.md` for the full evidence, including
real queries where duplicate copies of the same file crowded out distinct results.

### After archive exclusion + content dedup

Same command, same machine, after both changes:

- **1,377 live (non-archive) documents**, resolving to **1,159 distinct content hashes**
  (218 of the 1,377 are duplicates of a hash already covered by another live document).
- **8,947 chunks, all embedded** — down from 17,611 (~49%), because duplicate content is chunked
  and embedded once regardless of how many paths share it.
- **DB size: 37 MB** (down from 71 MB; `VACUUM` reclaims the migration's freed pages).
- **Cold index time: 1m 48s** (down from 4m 9s — roughly 2.3x faster).
- **Incremental re-index (2 new files added, nothing else touched): 1.13 seconds** (was 1.49s on
  the pre-dedup schema at a larger corpus — no regression; a plain no-op re-index over the full
  1,377-document corpus is ~1.1s, dominated by loading the embedding model, not by any per-file
  work).
- **`find` is untouched**: still walks live, still includes `archive/`, still ~0.1s over the whole
  tree (verified below with a string duplicated across both live and archived copies).

### Duplicate-crowding check — before vs. after

The two queries from the corpus evidence, re-run after dedup, top 5 each:

```
$ doc-indexer search "why does the login screen fail the first time"
0.606  docs/machines/2026_09_06_xorg_greeter_crash_rrtellchanged.md:16-40
       On boot, the GNOME login screen fails on the first attempt and bounces back to the
       greeter. The second attempt always succeeds. …
0.497  docs/auto-doc/gherkin.md:253-289
       @negative Scenario: Login fails with incorrect password …
0.356  docs/wiki/core_concepts/development/security/passkey.md:66-76  (+1 identical copies)
       Device Signs Challenge: The device uses the private key to sign the challenge, proving …
0.356  docs/machines/2026_09_06_nvidia_module_missing_hdmi_not_detected.md:159-177
       The package postinstall loaded nvidia and nvidia_drm …
0.345  embedded/media-remote/docs/issues/2026_06_13_ble_hid_remote_resets_then_no_input.md:13-24
       The board was in a continuous boot loop …
```

`passkey.md` now occupies exactly one slot (with a `(+1 identical copies)` note for the one
remaining live duplicate; the three `archive/` copies are excluded from search entirely), instead
of three of five slots as in the pre-dedup evidence.

```
$ doc-indexer search "USB Type A connector pinout and orientation"
0.709  docs/wiki/3d_scanner/electrical_connectors/usb_a.md:1-30
0.652  docs/wiki/3d_scanner/electrical_connectors/usb_b.md:1-31
0.636  docs/wiki/3d_scanner/electrical_connectors/usbc.md:1-29  (+1 identical copies)
0.629  docs/wiki/3d_scanner/electrical_connectors/micro_usb.md:216-238  (+1 identical copies)
0.628  embedded/led-vu-meter/.claude/skills/kicad/references/schematic-analysis.md:880-892
```

`usb_a.md` appears once, at rank 1, not twice at identical score.

`find` still returns every path for duplicated content, `archive/` included — confirmed with a
phrase from `passkey.md` unique enough to avoid false positives:

```
$ doc-indexer find "proving ownership of the public key"
archive/wiki-demo/markdown_renderer/public/wiki/.../passkey.md
archive/wiki-demo/wiki/.../passkey.md
archive/wiki-demo/wiki_demo.wiki/.../passkey.md
docs/wiki/core_concepts/development/security/passkey.md
meta/markdown-renderer/public/wiki/.../passkey.md
```

All 5 copies, exactly as before dedup — `find` never deduplicates or excludes archive.

## How an agent should use this

- Prefer `find` for "does X appear anywhere / where exactly" — it's instant, always current, and
  needs nothing set up.
- Use `search` for "what do we already know about X" when the phrasing won't literally match —
  concept/paraphrase lookups, prior-art checks before starting domain work (per `CONVENTIONS.md`
  §5's "recall before non-trivial domain work").
- Always read the path in a result before trusting it — it tells you the domain/project scope
  (e.g. `robotics/docs/notes/...` vs `automotive/gyopart/docs/decisions/...`) without opening the
  file.
- Re-run `index <base-dir>` after any session that added or edited markdown you want searchable —
  it's cheap when nothing changed (a few hundred ms of stat calls) and only pays the embedding
  cost for what actually changed.
- If `search` reports embeddings are unavailable, that's a real "can't do this," not a bug to work
  around — fall back to `find`, or run `install-embeddings.sh` if you have shell access to fix it
  properly.
- `search` never covers `archive/` unless it was indexed with `--include-archive` — if you're
  specifically researching *why* something was retired or superseded, `find` still reaches
  `archive/` (it never excludes anything), so use that instead of assuming `search`'s silence means
  no history exists.
- A `search` result's `(+N identical copies)` note means exactly that: identical bytes at N other
  paths. If which specific path matters (not just the content), follow up with `find` on a phrase
  from the excerpt to get the full list.

## Deliberately out of scope

- No server, no daemon, no HTTP API — everything is a one-shot CLI invocation.
- No note-taking, no todos, no tool-doc scraping, no cross-machine sync. Those are exactly the
  services this tool replaces; adding their features back in would recreate the sprawl.
- No vector database dependency (see above).
- Not a full `.gitignore` implementation — common patterns (plain names, simple globs, trailing
  `/` for dir-only, leading `/` for anchoring) are honored; negation (`!pattern`) and other edge
  cases are not. This is stated as a design constraint ("follow `.gitignore` where practical"), not
  an oversight.
