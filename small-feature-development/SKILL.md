---
name: small-feature-development
description: 'Lightweight development workflow for small, well-defined tasks that do not need planning or brainstorming. Use when the ask is a focused change: a bug fix, config update, adding a field, renaming something, updating a note, adding a single endpoint, or any task completable in under 10 file edits without architecture decisions.'
---

# Small Feature Development

A streamlined workflow for tasks that are too small to warrant a plan. Execute immediately,
test, done. No spec documents, no brainstorming, no planning phases.

---

## Is This Task Small Enough?

**Use this skill** (execute immediately):
- Bug fix in a known location
- Config or values change
- Adding/renaming a field or endpoint
- Updating a note, skill, or document
- Any change touching fewer than ~5 files with no architecture decisions

**Switch to brainstorming** if the task:
- Requires designing something new with non-obvious tradeoffs
- Touches more than ~5 files or multiple systems
- Has open design questions that need answering before coding

---

## Workflow

1. **Read the relevant files** — understand what exists before touching anything
2. **Make the change** — write code directly, no intermediate documents
3. **Test** — run the appropriate check (tests, build, smoke test, manual verify)
4. **Done** — report what changed and where

---

## Context Watchdog

After every 5 tool calls, pause briefly and estimate how full the context window is based
on conversation length. If it feels past ~70%:

1. Finish the current atomic step — do not stop mid-edit
2. Invoke the `handoff-document` skill to write a handoff
3. Stop and tell the user the handoff is ready for the next session

**Never** pass code through a handoff document or context store. File paths only —
the next agent reads the files directly.

---

## Rules

- No planning documents, no spec files, no brainstorming phase
- Write code immediately — do not stage it in notes, context store, or handoff docs
- If you realize mid-task the scope is larger than expected, stop, tell the user, and suggest switching to brainstorming
- Context store and notes are for discoveries and findings, never for code or file contents
