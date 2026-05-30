---
name: workflow-analysis
description: 'Analyze a UI or system for workflow coverage and usability gaps. Use when asked to analyze a UI, review a system for usability, or produce a workflow coverage report. Output is a structured, opinionated report with prioritized gaps.'
---

# Workflow Analysis

Analyze a UI or system for real workflow coverage. The goal is a structured, honest report
that identifies what actually works, what is broken, what is missing, and what is so bad the
user will route around it rather than fix it.

**Default posture: assume nothing works until proven otherwise.** "Mostly built out" is not
a verdict. A workflow that requires copy/pasting IDs, switching sections to look something up,
or that silently fails is a broken workflow — not an incomplete one.

---

## Phase 1 — System Inventory

Before evaluating any workflow, build a complete inventory of what exists.

### 1a. Entity map

List every entity the system manages. For each entity, record:

| Entity | Fields (all of them) | CRUD ops exposed in UI | CRUD ops missing from UI |
|--------|---------------------|------------------------|--------------------------|

Pull this from the backend schema/models, not just the UI. The UI may omit fields that the
backend supports — that is a gap.

### 1b. Relationship map

List every relationship between entities (one-to-many, many-to-many, foreign keys). For each:

- Can the relationship be established from the UI?
- Can the relationship be browsed (see linked items inline)?
- Can the relationship be removed from the UI?
- Does establishing the relationship require the user to know or type a raw ID/slug?

A relationship that requires the user to copy/paste an identifier is **broken**.

### 1c. Navigation inventory

List every navigation path in the UI:

- Sidebar items, tabs, links, buttons that change the visible section
- Any duplicate paths to the same destination (Workday syndrome: automatic failure)
- Any destination reachable only by one specific path with no shortcut or back-navigation

### 1d. Filter and search inventory

For every list in the UI, record:

- Does it have a filter or search?
- If not, how many items could it realistically contain in production use?
- Do filters persist when the user navigates away and back?
- Is any list driven by state from a completely different section? (anti-pattern — document it)

---

## Phase 2 — Persona and Workflow Identification

### 2a. Identify personas

Identify the distinct user roles or modes of working. Typical examples:

- **Creator** — sets up projects, defines structure, writes specs
- **Worker** — picks up tasks, executes, records findings
- **Reviewer** — checks status, reviews output, closes items
- **Observer** — monitors dashboards, queries state, reads reports

Not every system has all of these. Use what applies.

### 2b. Enumerate workflows per persona

For each persona, enumerate every complete workflow they need to execute. A workflow is not
a feature — it is a start-to-finish interaction with a concrete outcome.

Write each as: **"[Persona] wants to [action] so that [outcome]"**

Examples:
- Worker wants to pick up the next available task so that they know what to work on
- Creator wants to create a task under a specific epic without leaving the projects page
- Reviewer wants to see all open issues linked to a specific task so that they can assess risk

Do not skip obvious workflows because they seem trivial. The obvious ones are usually broken.

### 2c. For each workflow, trace it through the UI

Walk the workflow step by step through the actual UI. Record:

1. **Starting point** — where does the user land to begin this workflow?
2. **Steps** — every click, form field fill, and navigation action required
3. **Breakpoints** — where does the workflow fail, require workaround, or become unclear?
4. **End state** — what does the UI show when the workflow completes successfully?
5. **Error path** — what happens if something goes wrong mid-workflow?

Rate each workflow:
- ✅ **Works** — completes end-to-end with no workaround, all fields available, clear feedback
- ⚠️ **Degraded** — completes but requires workaround, extra clicks, or copy/paste
- ❌ **Broken** — cannot complete without leaving the system, using raw API, or guessing

A ⚠️ is not acceptable as a final state. It means "broken in a survivable way."

---

## Phase 3 — Anti-Pattern Audit

Check explicitly for these anti-patterns. Each one found is a P0 or P1 gap.

### Form anti-patterns

- **Partial forms** — create/edit form does not expose all fields the backend accepts
- **Raw ID/slug inputs** — any field that requires the user to type or paste an entity
  identifier rather than selecting from a searchable dropdown
- **Silent validation** — form submits, nothing happens, no error shown
- **Reset on error** — form clears when submission fails, user loses entered data
- **No required field indicators** — user cannot tell what is required before submitting

### Navigation anti-patterns

- **Silent click** — clicking a list item collapses it or does nothing observable; user cannot
  tell if selection was registered
- **Orphaned selection** — user selects item A, navigates away, comes back and the selection
  is gone but the detail panel shows a stale item A
- **No close/dismiss** — panel or detail view has no obvious way to clear/close it
- **Missing breadcrumbs** — user is three levels deep in a hierarchy with no indication of
  where they are or how they got there
- **Duplicate menus** — two or more navigation elements offer the same or overlapping options
  from different places on the page

### Cross-entity anti-patterns

- **Linked items hidden behind navigation** — to see issues linked to a task, the user must
  leave the task and navigate to Issues, then filter manually
- **Context lost in linked section** — user clicks "view issues for this task" and lands in
  Issues with no filter applied, showing all issues
- **Manual relationship wiring** — creating a design doc linked to an epic requires the user
  to (1) create the doc, (2) navigate to the epic, (3) paste the doc ID
- **No inline creation** — to link a new issue to a task, the user must create the issue
  separately, navigate back, and then link it

### List and filter anti-patterns

- **Unbounded lists with no filter** — any list that has no search/filter and will grow in
  production
- **Filter reset** — filters clear when the user navigates away and returns
- **Cross-section filter dependency** — a list in section B is only useful if the user already
  knows an ID from section A (Brief Viewer driven by manually pasted task slug is a canonical
  example of this failure)

### State and feedback anti-patterns

- **No empty state** — list is blank with no explanation or call to action
- **No loading state** — panel is blank while data loads; user cannot distinguish "loading"
  from "empty"
- **No success feedback** — form submits successfully and nothing changes visibly
- **No error feedback** — request fails silently; user resubmits thinking it didn't send
- **Stale list after mutation** — create/edit/delete completes but the list does not reflect
  the change until the user manually refreshes

### Keyboard and accessibility anti-patterns

- **Broken tab order** — tabbing skips interactive elements or jumps non-sequentially
- **No Enter-to-submit** — form fields do not submit the form on Enter
- **No Escape-to-dismiss** — modals and panels do not close on Escape
- **Focus lost on open/close** — opening a modal moves focus into it; closing it drops focus
  to the top of the page instead of back to the trigger element

---

## Phase 4 — Report

Structure the output as a markdown document saved to `docs/workflow-analysis-YYYY-MM-DD.md`
in the project repo (create `docs/` if absent).

### Report structure

```markdown
# Workflow Analysis — <System Name>
**Date:** YYYY-MM-DD
**Verdict:** FAILS BASELINE / PASSES BASELINE (few things fail baseline — be honest)

## Summary
One paragraph. Be direct. Describe the overall state of the system from a real user's
perspective. If it's bad, say it's bad. Do not soften.

## Baseline Checklist Results
Table with every baseline item (from ui-development skill), Pass/Fail, and a one-line note.
Fail means fail — not "partial" or "mostly."

## Entity + Relationship Coverage
From Phase 1. What's exposed, what's missing.

## Workflow Coverage by Persona
For each persona: table of workflows with ✅/⚠️/❌ status and a short description of what
is broken or degraded.

## Anti-Pattern Audit Results
For each anti-pattern found: which section it appears in, specific element or interaction,
severity (P0 / P1 / P2).

## Prioritized Gap List

### P0 — Workflow Blockers (cannot complete workflow without workaround)
Numbered list. Each item: entity/section affected, what is broken, what the correct behavior
should be.

### P1 — High Friction (workflow completes but is painful, unclear, or requires extra steps)
Same format.

### P2 — Polish (minor UX issues that do not impede workflows)
Same format.

## Recommendations
For each P0 and P1, a concrete recommendation. Not "improve the form" — instead: "Add a
searchable dropdown for `epic_slug` on the task create form, populated from GET /epics with
live search filtering by title. Remove the raw text input."
```

---

## Rules

- Report must include a baseline checklist table with explicit Pass/Fail for every item —
  no "N/A" unless the item genuinely does not apply to the system type
- A workflow rated ✅ must have been traced step by step through the actual UI, not assumed
  to work based on the presence of a form
- Do not soften findings for tone. "The user must copy and paste a task slug to use the Brief
  Viewer" is the correct finding, not "the Brief Viewer has limited search functionality"
- Recommendations must be specific and actionable — reference actual endpoints, field names,
  and UI locations
- Save the report to the project's docs folder and commit it; do not leave it only in context
