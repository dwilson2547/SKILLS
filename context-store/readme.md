# Playbooks Server — Requirements

Companion service to `ai_notes_server`. Where notes are minimal, high-signal lookups,
playbooks are structured reference documents — plans, strategies, multi-step procedures —
that agents author once and retrieve selectively across sessions.

---

## Concept

**Notes** → what agents have learned (agent-written, minimal, lookup-optimized)  
**Playbooks** → reference material agents consult (structured, section-retrievable, human or agent authored)

Notes should pointer-reference playbooks where relevant. The standard pattern is:

> Note: "junkyard scraper auth strategy documented — query playbooks slug `junkyard-scraper/auth` for full detail"

This keeps notes lean and lets agents decide whether they need the full document before spending tokens on it.

---

## Stack

Mirror the notes server stack for consistency and minimal ops overhead:

- **API** — FastAPI + SQLite + `fastembed` (`BAAI/bge-small-en-v1.5` via ONNX — no PyTorch)
- **UI** — Alpine.js SPA served by nginx (read/browse only, no authoring UI required initially)
- **Data** — `./data/playbooks.db` (SQLite, persisted via volume mount)
- **Ports** — API `:8001`, UI `:3001` (avoids collision with notes server)
- **Deployment** — `docker-compose.yml` matching notes server conventions

---

## Data Model

### Document

| Field | Type | Notes |
|---|---|---|
| `id` | integer PK | auto |
| `slug` | text unique | path-like, e.g. `junkyard-scraper/auth` |
| `title` | text | human-readable display name |
| `description` | text | one-line summary of purpose |
| `tags` | text | comma-separated, same convention as notes |
| `session_id` | text | optional — session that produced the document |
| `supersedes` | text | slug of document this replaces, if any |
| `status` | text | `active` \| `stale` — stale docs remain queryable but are deprioritized |
| `created_at` | timestamp | |
| `updated_at` | timestamp | |

### Section

Parsed from document markdown at ingest time. Not user-managed directly.

| Field | Type | Notes |
|---|---|---|
| `id` | integer PK | auto |
| `document_id` | FK → Document | |
| `slug` | text | e.g. `junkyard-scraper/auth#authentication-flow` |
| `heading` | text | heading text as written |
| `level` | integer | 1–6 (H1–H6) |
| `content` | text | raw markdown content of this section |
| `embedding` | blob | fastembed vector for semantic search |
| `position` | integer | order within document |

---

## Document Hierarchy via Slugs

Slugs are path-like and define parent/child relationships implicitly.

```
junkyard-scraper
junkyard-scraper/auth
junkyard-scraper/sites/pull-a-part
junkyard-scraper/sites/lkq
```

No foreign key hierarchy is needed — slug prefix matching handles tree traversal.
Agents construct slugs deliberately; when unsure, they should check existing slugs first
or clarify with the user before ingesting.

**Slug rules:**
- Lowercase, hyphen-separated words
- `/` as hierarchy separator
- No spaces, no special characters beyond `-` and `/`
- Max depth: 4 levels (enough for any real use case)

---

## API Endpoints

### `GET /instructions`
Agent onboarding. Returns a concise description of what playbooks are, when to use them
vs notes, and the complete workflow in minimal prose. This is the first call any agent
should make.

### `POST /playbooks`
Ingest a new document.

Request body:
```json
{
  "slug": "junkyard-scraper/auth",
  "title": "Junkyard Scraper — Auth Strategy",
  "description": "OAuth and session handling patterns for yard management sites",
  "content": "# Auth Strategy\n\n## Overview\n...",
  "tags": "scraper,auth,junkyard",
  "session_id": "abc123",
  "supersedes": null
}
```

- `slug` and `content` are required; all other fields optional
- `slug` must be unique — returns `409` if already exists (use `PUT` to update)
- Content is parsed into sections at ingest; embeddings generated immediately
- If `supersedes` is provided, the referenced document is marked `stale`

### `PUT /playbooks/{slug}`
Replace content of an existing document. Re-parses and re-embeds all sections.
Does not change slug, title, tags, or session_id unless explicitly provided.

### `GET /playbooks/{slug}`
Return document metadata + full content. Use sparingly — prefer section retrieval.

Response includes:
```json
{
  "slug": "junkyard-scraper/auth",
  "title": "...",
  "description": "...",
  "tags": "...",
  "status": "active",
  "created_at": "...",
  "updated_at": "...",
  "content": "..."
}
```

### `GET /playbooks/{slug}/toc`
Return the section map for a document without content. Cheap call — agents should
use this before deciding which section to retrieve.

Response:
```json
{
  "slug": "junkyard-scraper/auth",
  "title": "...",
  "description": "...",
  "sections": [
    { "heading": "Overview", "level": 1, "slug": "junkyard-scraper/auth#overview", "position": 0 },
    { "heading": "OAuth Flow", "level": 2, "slug": "junkyard-scraper/auth#oauth-flow", "position": 1 },
    { "heading": "Session Handling", "level": 2, "slug": "junkyard-scraper/auth#session-handling", "position": 2 }
  ]
}
```

### `GET /playbooks/{slug}/sections/{section_slug}`
Return content of a single section only.

Response:
```json
{
  "heading": "OAuth Flow",
  "level": 2,
  "content": "...",
  "position": 1
}
```

### `GET /playbooks`
List all documents. Supports filtering.

Query params:
- `tags` — comma-separated tag filter (AND)
- `scope` — slug prefix filter, e.g. `scope=junkyard-scraper` returns all documents under that tree
- `status` — `active` (default) \| `stale` \| `all`
- `session_id` — filter by originating session

Response: array of document metadata (no content, no sections).

### `GET /playbooks/{slug}/children`
Return immediate children of a slug in the hierarchy.

```
GET /playbooks/junkyard-scraper/children
→ [junkyard-scraper/auth, junkyard-scraper/sites]
```

### `POST /playbooks/search`
Semantic search across all section embeddings. Returns matching sections with their
parent document context.

Request:
```json
{
  "query": "how to handle OAuth token refresh",
  "scope": "junkyard-scraper",
  "limit": 5,
  "status": "active"
}
```

Response:
```json
[
  {
    "document_slug": "junkyard-scraper/auth",
    "document_title": "...",
    "section_heading": "OAuth Flow",
    "section_slug": "junkyard-scraper/auth#oauth-flow",
    "score": 0.91,
    "preview": "first 200 chars of section content..."
  }
]
```

`scope` is optional — omit to search all documents. Stale documents excluded by default.

### `DELETE /playbooks/{slug}`
Hard delete a document and all its sections. Use `supersedes` on ingest for soft
deprecation instead — prefer that pattern for anything that might be referenced by notes.

### `PATCH /playbooks/{slug}/status`
Explicitly mark a document `active` or `stale` without replacing it.

---

## CLI

Matches notes server CLI conventions. All commands interact with the API — no direct DB access.

```bash
# Ingest a file
playbooks ingest plan.md --slug "junkyard-scraper" --description "Site scraping master plan" --tags "scraper,junkyard"

# Ingest with session tracking
playbooks ingest auth.md --slug "junkyard-scraper/auth" --session abc123

# List all active playbooks
playbooks ls

# List within a scope
playbooks ls --scope junkyard-scraper

# Show TOC for a document (cheap — use before get)
playbooks toc junkyard-scraper/auth

# Get full document
playbooks get junkyard-scraper/auth

# Get a specific section
playbooks get junkyard-scraper/auth#oauth-flow

# Semantic search
playbooks search "token refresh handling" --scope junkyard-scraper

# Check existing slugs (agents should run this before ingesting)
playbooks slugs
playbooks slugs --scope junkyard-scraper

# Mark stale
playbooks stale junkyard-scraper/auth

# Delete
playbooks delete junkyard-scraper/auth

# Replace content from file
playbooks update junkyard-scraper/auth --file updated-auth.md
```

---

## Section Parsing Rules

Sections are split at markdown headings (`#` through `######`). Each heading and all
content until the next heading of equal or lesser depth is one section.

- A document with no headings is stored as a single section
- Heading text is stripped of markdown formatting for the `heading` field
- Embeddings are generated from `heading + "\n\n" + content` to preserve context
- Empty sections (heading with no content before next heading) are stored but not embedded

---

## Agent Skill (`SKILL.md`)

Located at `SKILL/playbooks/SKILL.md`. Should cover:

**When to use playbooks vs notes:**
- Notes: single lookup facts, patterns, pointers — always minimal
- Playbooks: multi-section documents, plans, strategies, procedures
- If it needs headers, it's a playbook

**Required workflow before ingesting:**
1. Run `playbooks slugs` to check what exists
2. If a related document exists, consider whether this extends it (new child slug) or replaces it (`--supersedes`)
3. If unsure of slug, ask the user before ingesting
4. After ingesting, save a pointer note: `"[topic] strategy documented — playbooks slug: [slug]"`

**Required retrieval workflow:**
1. Check notes first — note may contain a direct slug pointer
2. If no pointer, run `playbooks search "[query]"` to find relevant sections
3. Run `playbooks toc [slug]` to review structure before pulling full content
4. Pull only the section(s) needed — avoid `playbooks get` unless the full document is necessary

**Do not:**
- Ingest scratchpad content or session logs — playbooks are reference documents, not history
- Use playbooks as a substitute for notes — keep learnings in notes, procedures in playbooks
- Ingest without a slug — always name things deliberately

---

## Recommended Workflow Integration with Notes

When closing a session that produced a playbook:

1. Agent ingests the document to playbooks with an appropriate slug
2. Agent saves a compact note pointing to it: `"auth strategy for yard management OAuth sites — see playbooks: junkyard-scraper/auth"`
3. Future agents query notes, find the pointer, pull only the relevant section from playbooks

This keeps the notes store as the single query entry point while offloading large content
to playbooks where it belongs.

---

## Out of Scope (v1)

- Agent write access to modify individual sections (full document replace via `PUT` only)
- Automatic TTL or expiry on documents
- Cross-document semantic linking
- Retrieval frequency tracking
- UI authoring — browse and search only