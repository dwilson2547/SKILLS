---
name: ai-notes-server
description: >
  DEPRECATED — the notes service stack (ai-notes-server, workman notes, context-store
  playbooks, todo store) is retired. Notes are now repo-native files under
  <domain>/docs/notes/ managed by meta/bin/wsnote in the workspace superrepo. If invoked,
  follow the workspace-conventions skill instead.
  Trigger phrases: check notes, save findings, persist knowledge, notes server.
applyTo: "**"
---

# Notes — RETIRED (repo-native now)

> ⚠️ **The entire notes/playbooks/todo service stack is retired** (2026-07). Do not use
> `workman note`, the `notes` CLI, `playbooks`, `todo`, or any localhost note endpoints.

Knowledge now lives in the workspace repo itself (CONVENTIONS.md §5):

- **Atomic notes** → `<domain>/docs/notes/` or `<project>/docs/notes/`, managed by
  **`meta/bin/wsnote`** (`add` / `search` / `ls` / `reindex`).
- **Long-form guidance** → `<domain>/docs/topics/`.
- **Backlogs** → `TODO.md` at project root.

Recall/save rules (the save gate, one-note-per-task, secondary domains) live in the
**workspace-conventions** skill — use that.
