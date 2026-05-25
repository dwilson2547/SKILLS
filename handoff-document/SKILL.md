---
name: handoff-document
description: 'Write a handoff document when context is running low and work is incomplete, or when explicitly requested. Never include code — pass file paths only.'
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

## Rules

- **No code.** The next agent reads the files directly. File paths only.
- Be specific enough that the next session requires zero clarification to resume.
- If open design decisions exist, list them first — they block everything downstream.
