---
name: handoff-document
description: 'Write a handoff document when incomplete work is being passed to someone else — stopping for the day, switching machines, or handing to another person or session. Use when explicitly asked for a handoff. Never include code — pass file paths only. Do NOT use this to pre-empt running out of context: the harness summarises and carries context forward on its own, so ending a session early for that reason wastes the work in progress.'
---

# Handoff Document

Write the handoff to `docs/handoff-<feature-name>.md` in the project root.

## Format

```
# Handoff: <Feature Name>

## What Was Completed
- Bullet list of steps finished in this session.

## What Remains
- Ordered list of remaining steps, specific enough to resume without re-reading the chat.

## Design Decisions Made
- Each significant decision and the rationale behind it.

## Open Design Decisions
- Unresolved decisions, options considered, and relevant tradeoffs.
- Flag these clearly — an unresolved decision is more dangerous than incomplete code.

## Files Modified
- List of files created or changed, with a one-line description of what changed.

## Suggested Starting Point
- Where the next session should begin: file path, function name, or step.
```

## When NOT to write one

Not because context is filling up. Long conversations are summarised and carried into the next
window automatically, so stopping to hand off mid-task ends a session that had no need to end. Write
one when the work is genuinely changing hands — a different day, a different machine, a different
person — not to pre-empt a limit the harness already handles.

## Rules

- **No code.** The next agent reads the files directly. File paths only.
- Be specific enough that the next session requires zero clarification to resume.
- If open design decisions exist, list them first — they block everything downstream.
