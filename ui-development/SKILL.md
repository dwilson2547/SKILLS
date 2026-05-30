---
name: ui-development
description: 'Build or improve a UI. Use when the user asks to create a UI, build a frontend, add a management interface, or improve an existing UI. Applies to any framework.'
---

# UI Development

UIs are built around user workflows, not API surface area. The first thing to establish is
what the user actually needs to do — not what the backend can do.

---

## Analysis Posture — Default to "This Is Bad"

When asked to analyze an existing UI, the default verdict is **"this UI does not meet baseline
usability requirements"** unless it demonstrably clears every item in the checklist below.
Optimistic assessments are harmful. "Mostly built out" or "mostly functional" are not
acceptable conclusions — they create false confidence and delay real fixes. Err on the side
of calling things broken. If you are not sure whether something is broken, it is broken.

### Baseline criteria (all required — no partial credit)

**Data entry:**
- [ ] Every entity create/edit form exposes all fields that the backend accepts
- [ ] Foreign key fields use a searchable dropdown populated from live data — not a raw text input requiring the user to know or copy/paste a slug/ID
- [ ] Required fields are visually distinguished from optional ones
- [ ] Validation errors surface inline, not silently dropped or shown only in the console

**Navigation and context:**
- [ ] Clicking any interactive element produces immediately obvious feedback — selection is highlighted, a panel opens, or navigation occurs; never a silent tree collapse
- [ ] The user can always see which item is currently selected/active without having to remember what they clicked
- [ ] Breadcrumbs or equivalent context indicators show where the user is in the hierarchy at all times
- [ ] The user can close, dismiss, or clear any panel, modal, or detail view without refreshing the page

**CRUD completeness:**
- [ ] Every entity can be created, read, edited, and archived/deleted from the UI without leaving the relevant section
- [ ] Archive/delete actions require confirmation before executing
- [ ] After create/edit/delete, the list refreshes immediately without a manual page reload

**Cross-entity linking:**
- [ ] Linked entities (issues on a task, design docs on an epic, etc.) are visible inline on the parent record — not only accessible by navigating to a separate section
- [ ] Creating a linked entity from within a parent record pre-populates the parent reference — the user never manually types or pastes a slug or ID to establish a relationship
- [ ] Filtering/searching in one section respects context from another (e.g., "show issues for this task" not "show all issues")

**Keyboard and accessibility:**
- [ ] All interactive elements are reachable and operable by keyboard (tab index is logical, no tab traps)
- [ ] Forms can be submitted with Enter; modals can be dismissed with Escape
- [ ] Focus is managed on panel open/close so the user's position is not lost

**Navigation consistency:**
- [ ] One and only one navigation pattern exists per type of destination — duplicate menus offering overlapping functionality is an automatic failure
- [ ] Settings and global controls live in one place and are accessed the same way everywhere
- [ ] Section transitions are predictable; the user is never surprised by where a click lands them

**Filters and search:**
- [ ] Every list that can grow beyond ~10 items has a filter or search control
- [ ] Filters persist within a session — switching sections and back does not reset them
- [ ] The Brief Viewer and any other cross-entity views have their own filter controls; the user never copies and pastes an ID from another section to drive them

**Empty and error states:**
- [ ] Every list has a non-blank empty state that tells the user what to do next
- [ ] API errors surface as visible feedback — not silently swallowed
- [ ] Loading states exist so the user is not staring at a blank panel wondering if it worked

---

If any item above is not met, the analysis **must** flag it as a failure item, not a
"nice-to-have" or a "P2." Items that block normal task completion are P0. Items that require
unnecessary clicks or manual work-arounds are P1. Purely cosmetic or minor polish items are
P2, but they still go in the report.

---

## Step 1 — Workflow Elicitation

Before touching any code, ask the user to describe how they will use the UI. Prompt with:

- What are the main tasks you need to accomplish?
- What does a typical session look like start to finish?
- Are there power-user flows vs casual-use flows?
- What would frustrate you most if it were missing or hard to find?

Compile the answers into a numbered workflow list and present it back:

```
Workflows:
1. <workflow name> — <one sentence description>
2. ...
```

**Do not proceed until the user approves this list.** Missing or wrong workflows discovered
after implementation are expensive. Get them right here.

---

## Step 2 — Identify What Each Workflow Needs

For each approved workflow, identify before writing code:
- What data is displayed
- What actions the user can take
- What the empty state looks like (no data yet)
- What the error state looks like (request failed, validation error, etc.)
- What success/confirmation feedback looks like

These are not optional. Empty and error states are part of the workflow, not polish.

---

## Step 3 — Implement One Workflow at a Time

Take the first workflow from the approved list. Implement it completely:
- The happy path
- The empty state
- The error state
- Any confirmation feedback

Then verify it (Step 4) before moving to the next workflow. Do not batch-implement multiple
workflows and verify later — a workflow is not done until it has passed verification.

---

## Step 4 — Verify Each Workflow with Playwright

Start the dev server, then navigate through the workflow end-to-end using Playwright.

For each workflow, verify:
- [ ] Happy path completes without errors
- [ ] Empty state renders correctly when there is no data
- [ ] Error state renders correctly when a request fails
- [ ] User receives clear feedback on success and failure actions

**If you are uncertain how to locate an element, trigger a state, or verify a behavior —
stop and ask the user before proceeding.** Do not guess at selectors, invent workarounds,
or mark a step as verified if you could not actually confirm it. A skipped or faked
verification is worse than an unverified one — it creates false confidence.

Example blockers to escalate:
- Element has no stable selector (no id, no aria label, class names look generated)
- Cannot determine how to trigger an error state without backend manipulation
- Unclear whether a UI update is the result of the action or pre-existing state

---

## Step 5 — Repeat for Remaining Workflows

Return to Step 3 for the next workflow. Continue until every approved workflow has been
implemented and verified.

Only declare the UI complete when every workflow on the approved list has passed Step 4.

---

## Rules

- Never start coding before the workflow list is approved
- Never move to the next workflow before the current one is verified
- Empty and error states are not optional — they are part of every workflow
- If Playwright verification is ambiguous or blocked, ask the user — do not resolve it unilaterally
- Do not ship placeholder data, stub interactions, or console.log-driven "verification"
- Framework agnostic — follow whatever stack is already in use; for greenfield, ask the user
- "Mostly working" is not working. A workflow that requires the user to copy/paste IDs, manually
  sync state between sections, or work around missing fields is **broken**, not "mostly working."

---

## Documentation Closure

Before declaring the task complete, scan the work you just did for anything worth capturing.

**Issue docs** — create `docs/issues/YYYY_MM_DD_<slug>.md` in the project repo for:
- Any build error, peer dep conflict, or missing package that wasn't obvious upfront
- Any framework/library behavior that contradicted documentation or expectations
- Any step you had to retry or that failed before succeeding

**Patterns docs** — add a section to `docs/<technology>_patterns.md` (create if absent) for:
- Any version constraint or peer dep incompatibility that bit you
- Any non-obvious framework or library pattern discovered during implementation

**Notes** — for any new or updated doc, add or update a note pointing to it:
```bash
notes add "title" "2-5 sentence summary. See: docs/<file>.md" --tags technology,project
```

**Skip this step only if** the change was purely mechanical with no debugging or surprises.
