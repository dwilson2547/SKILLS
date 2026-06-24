---
name: context-store
description: >
  PROACTIVE SKILL — invoke this skill whenever you produce or update any structured document with
  headers (plans, strategies, architecture docs, procedures, guides, implementation plans, scraper
  strategies, site-specific patterns). Do NOT wait to be asked. If you wrote a plan.md, a strategy,
  or any multi-section content this session, ingest it into context before the session ends and
  update the associated note. Also invoke when retrieving an existing strategy or procedure.
  The Context Store (http://localhost:8001) is the living source of truth for structured knowledge.
applyTo: "**"
---

# Context Store

Structured reference documents for AI agents. Where notes store minimal one-off facts,
Context Store holds multi-section documents that agents consult selectively.

> If `context` is not installed, follow [INSTALL.md](./INSTALL.md). If the CLI is unusable, see [FALLBACK.md](./FALLBACK.md) for curl commands.

---

## Notes vs Context docs

| | Notes | Context docs |
|---|---|---|
| **Content** | 2–5 sentences, one fact | Multi-section markdown document |
| **When to use** | Learnings, gotchas, pointers | Plans, strategies, procedures |
| **Authored by** | Agent (always) | Human or agent |
| **Retrieved by** | Keyword/semantic search | Slug pointer → TOC → section |

**Rule of thumb:** if it needs headers, it's a context doc.

---

## When to Use

### Always Ingest (no prompt needed)

These situations require ingestion without waiting for user instruction:

- You produced a **plan, strategy, architecture doc, or procedure** with multiple sections during this session
- You wrote a **plan.md** or equivalent structured document as part of your work
- You made **significant implementation decisions** that future agents would benefit from knowing
- A **scraper, service, or feature** has a site-specific strategy or multi-step approach that took effort to develop
- The session is ending and you generated any structured content that hasn't been ingested yet

> **Context docs are an extension of agent memory.** If you don't ingest it, it's lost. Don't wait for the user to ask.

### Always Update (when content changes)

- You revised a plan or strategy already stored as a context doc → run `context update <slug> --file <updated-file>`
- You completed a phase described in a context doc → update the relevant section so future agents see current state
- A previously documented approach was found to be wrong or outdated → update or mark stale

### Retrieve a context doc when:
- A note contains a slug pointer to a context doc
- You need a full procedure, not just a one-liner fact
- Semantic search returns a section result pointing to a context doc

---

## CLI Usage

```bash
# Before ingesting — always check what exists
context slugs
context slugs --scope junkyard-scraper

# Ingest a new context doc from a file
context ingest auth.md --slug "junkyard-scraper/auth" --description "OAuth and session handling" --tags "scraper,auth"

# Replace content (re-parses all sections)
context update junkyard-scraper/auth --file updated-auth.md

# List documents
context ls
context ls --scope junkyard-scraper
context ls --status stale

# Browse structure — cheap, do before get
context toc junkyard-scraper/auth
context children junkyard-scraper

# Retrieve content
context get junkyard-scraper/auth              # full document
context get junkyard-scraper/auth#oauth-flow   # single section only

# Semantic search (searches section embeddings)
context search "token refresh handling" --scope junkyard-scraper
context search "cloudflare bypass" --limit 10

# Deprecate
context stale junkyard-scraper/auth
context activate junkyard-scraper/auth

# Delete (hard — prefer stale for anything referenced by notes)
context delete junkyard-scraper/auth
```

---

## Slug Rules

- Lowercase, hyphen-separated words: `junkyard-scraper/auth`
- `/` as hierarchy separator — max 4 levels
- No spaces, no special characters beyond `-` and `/`
- Slugs are permanent identifiers — choose deliberately

---

## Required Workflow: Ingesting

1. Run `context slugs --scope <relevant-scope>` to check what already exists
2. If a related document exists, decide:
   - **New child** — use a deeper slug (`junkyard-scraper/auth/oauth`)
   - **Replacement** — use `--supersedes old-slug` (marks old doc stale automatically)
   - **Update** — use `context update` instead of ingest
3. If unsure about the slug, ask the user before ingesting
4. After ingesting, check for an existing note before creating one:
   - `notes search "<topic>"` — look for a note already covering this subject
   - If a relevant note exists: `notes update <id> --content "<existing content>. See context: <slug>"` (append the pointer, preserve existing content)
   - If no note exists: `notes add "[topic]" "Detailed procedure documented. See context: <slug>" --tags <tags>`

---

## Required Workflow: Retrieval

1. Check notes first — a note may contain a direct slug pointer (cheapest path)
2. If no pointer, run `context search "<query>"` to find relevant sections
3. Run `context toc <slug>` to review structure before pulling full content
4. Pull only the section(s) needed — avoid `context get` unless the full document is necessary
5. Do not load the full document just to scan it — TOC + targeted section retrieval saves tokens

---

## Do Not

- Ingest scratchpad content, session logs, or in-progress notes — context documents are polished reference material
- Use context as a substitute for notes — keep learnings in notes, larger documents in Context Store
- Ingest without a slug — always name deliberately
- Use `delete` for documents referenced by notes — use `stale` instead

---

## Notes Integration Pattern

```
Session produces a multi-step strategy
  → Agent ingests to context: context ingest strategy.md --slug "topic/strategy"
  → Agent searches for existing note: notes search "topic strategy"
  → If found: notes update <id> --content "<existing content>. See context: topic/strategy"
  → If not found: notes add "topic strategy" "Full procedure documented. See context: topic/strategy" --tags topic

Future session needs the strategy
  → notes search "topic strategy"  → finds pointer note with slug
  → context toc topic/strategy   → reviews structure
  → context get topic/strategy#relevant-section  → pulls only what's needed
```
