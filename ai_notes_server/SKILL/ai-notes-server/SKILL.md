---
name: ai-notes-server
description: >
  Notes have migrated to Work Manager. Use `workman note` for all note operations — saving
  findings, searching domain knowledge, and surfacing gotchas. Notes saved here are auto-pulled
  into task briefs when scope tags overlap. Do NOT use the old `notes` CLI.
  Trigger phrases: check notes, save findings, persist knowledge, notes server.
applyTo: "**"
---

# Notes — Now in Work Manager

> ⚠️ **Migrated.** Notes have moved from the standalone AI Notes Server into Work Manager.
> Use `workman note` for all note operations. The old `notes` CLI and `http://localhost:8000`
> are legacy and should not be used.

Notes persist across sessions so agents can build on prior work instead of re-discovering
the same patterns. Notes saved with a `scope:` tag are automatically surfaced in task briefs
(`workman brief TASK-xxx`) when the task shares the same scope tags.

---

## When to Use

**Before starting a task** — run `workman brief TASK-xxx`. Relevant notes are auto-pulled into
the brief based on tag overlap. For ad-hoc lookup: `workman note list --query "topic"`.

**After resolving a non-obvious problem** — save findings before moving on.

**When discovering environment-specific behavior** — version quirks, toolchain gotchas, platform workarounds.

**Do not write a note for** — things easily found in official docs, routine tasks, or anything already noted.

---

## Usage

```bash
# Search
workman note list --query "cloudflare bypass playwright"

# Create — scope: tag required
workman note add --title "Title" \
  --body "2-5 sentences. Key facts. What worked. Specific details." \
  --tags "scope:scraping,cloudflare,playwright"

# View
workman note get NOTE-001
```

---

## Note Quality

- **Content:** 2-5 sentences. Facts and gotchas, not strategy. Max ~2000 characters.
- **Tags:** Must include at least one `scope:` prefixed tag (e.g. `scope:scraping`, `scope:kubernetes`,
  `scope:gyopart`, `scope:dev`). Add specifics after: `scope:scraping,cloudflare,junkyard`.
- The `scope:` tag controls which task briefs surface the note — choose it to match the domain.
- Prefer creating a new note over updating one from a different context.

---

## Escalate to Context Store

When saving a note, ask: *does this content have headers or span multiple steps?*

**If yes — ingest to context first, then add a pointer note in workman:**

```bash
# Write the structured content to a temp file, then ingest
context ingest /tmp/strategy.md --slug "scope/topic" --description "..." --tags "tag1,tag2"

# Then add a pointer note in workman
workman note add --title "Topic Strategy" \
  --body "Full procedure documented. See context: scope/topic" \
  --tags "scope:domain,tag1,tag2"
```

**Context Store is the living source of truth for structured documents.** If a plan or strategy was
updated this session, the context document must be updated too — don't let notes point to stale content.

Use `context update <slug> --file <file>` to keep context current whenever the underlying document changes.
