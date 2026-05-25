---
name: todo-store
description: >
  Use this skill when capturing, listing, updating, completing, importing, or exporting lightweight
  work items so bugs and follow-ups do not get lost during triage. Todo Store
  (http://localhost:8003) is the central backlog for ad-hoc tasks. Prefer the `todo` CLI for
  normal operations; use install or curl fallback only if the CLI is unavailable.
applyTo: "**"
---

# Todo Store

Todo Store is a lightweight backlog for AI agents. Use it to persist bugs, follow-ups, and loose
tasks that should survive beyond the current session.

> If `todo` is not installed, follow [INSTALL.md](./INSTALL.md). If the CLI is unusable, see
> [FALLBACK.md](./FALLBACK.md) for curl commands.

---

## When to Use

- The user calls out a bug, follow-up, or triage task that should not be lost
- You discover a side issue while debugging something else
- You need to reprioritize or close previously captured tasks
- You need to move tasks between environments with import/export

---

## CLI Usage

```bash
# List todos
todo ls
todo ls --status open --priority high
todo ls --query inventory --tags bug,triage

# Add a todo
todo add "Investigate flaky yard sync" \
  --description "Observed while debugging importer retries. See notes: yard-sync-retries" \
  --tags bug,triage \
  --priority high

# Read / update
todo get 42
todo update 42 --priority urgent --status in_progress
todo update 42 --description "Now blocked on upstream API response samples"

# Complete / reopen
todo done 42 --note "Fixed while working on retry handling"
todo reopen 42

# Delete
todo delete 42

# Export / import
todo export todos.json
todo import todos.json
todo import todos.json --mode replace
```

---

## Required Workflow

1. Before adding a new task, run `todo ls --query "<title words>"` to avoid obvious duplicates
2. When creating a task, include:
   - title
   - short description
   - tags
   - priority
3. Use `todo done <id> --note "..."` when closing work so the resolution is preserved
4. Use descriptions to point at related notes or context-store entries when helpful

---

## Do Not

- Use Todo Store as a replacement for notes or context-store
- Put multi-step strategy documents into Todo Store
- Leave priority unspecified when the user clearly implied urgency
