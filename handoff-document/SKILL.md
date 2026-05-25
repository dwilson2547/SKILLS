---

## Handoff Document

Produce this when context is running low before the work is complete, or when explicitly requested.

**Format — plain prose and lists, no code blocks.**

```
# Handoff: <Feature Name>

## What Was Completed
- Bullet list of steps finished in this session.

## What Remains
- Ordered list of remaining implementation steps, specific enough that
  a developer can pick up without needing to re-read this session's chat.

## Design Decisions Made
- List each significant decision and the rationale behind it.

## Open Design Decisions
- Any decisions that still need to be made before a remaining step can be implemented.
- Include the options considered so far and any relevant tradeoffs.

## Files Modified
- List of files created or changed, with a one-line description of what changed.

## Suggested Starting Point
- Where the next session should begin (file, function, or step).
```

**Rules for the handoff:**
- No code. The next agent will re-index the project and read the files directly.
- Be specific enough that the next session requires no clarification to resume.
- If there are open design decisions, flag them clearly — an unresolved decision is more dangerous than an incomplete implementation.
