---
name: ui-development
description: 'Build or improve a UI. Use when the user asks to create a UI, build a frontend, add a management interface, or rewrite an existing UI. Applies to any framework. For analysis-only tasks, use workflow-analysis instead.'
---

# UI Development

UIs are built around user workflows, not API surface area. Understand what the user needs to
do before writing any code.

---

## State File

Check for `.ui_dev_state.md` in the project root before doing anything else.

- **Exists:** read it, resume from the recorded step. Do not restart.
- **Does not exist:** create it now and proceed to Step 0.

```markdown
# UI Dev State
step: 0
mode: pending

## Workflows
(populated after Step 0 or Step 1)

## Verification
(populated after each workflow ships — "1. <name>: pass" or "fail — <reason>")
```

Update this file at the start of every step and after every verification. The file must
always contain the current step, the full workflow list with descriptions, and all
verification results. After context compaction this file is the only source of truth.

---

## Step 0 — Design Before Code

Before writing any code, answer these questions and **write the answers to
`.ui_dev_design.md`**. Do not hold design in reasoning — if it is not in the file, it does
not exist.

### If a workflow-analysis report exists (`docs/workflow-analysis-*.md`):

Read it. The report contains the workflow list, the gap analysis, and the prioritized fix
list. Extract:

1. The workflow list (from "Workflow Coverage by Persona") — these are your workflows.
2. The P0 and P1 gaps — these define what must be built or rebuilt.
3. The recommendations — these are your implementation specs.

Write to `.ui_dev_design.md`: the workflow list, what the primary use case is (one sentence,
from the user's perspective), and what the hero surface should be (the view that gets the
most screen real estate because it serves the 80% use case). Then skip to Step 2.

### If no report exists (greenfield or user-directed build):

Write to `.ui_dev_design.md`:

1. **What is this system for?** One sentence, from the user's perspective. Not "a task
   management system" — "a tool that lets a team pick up work, execute it, and record what
   they learned."
2. **What does the user do 80% of the time?** This is the hero flow. Everything else is
   secondary.
3. **What should the hero surface look like?** What gets the most real estate, what is one
   click away, what is hidden behind a button and why.
4. **What does the system already know?** Every field the user fills in that the system could
   infer or pre-populate is a design failure.

Then proceed to Step 1.

---

## Step 1 — Workflow Elicitation (greenfield only)

Skip this step if workflows came from a workflow-analysis report.

Ask the user to describe how they will use the UI:

- What are the main tasks you need to accomplish?
- What does a typical session look like?
- What would frustrate you most if it were hard to find?

Compile into a numbered workflow list. **Do not proceed until the user approves it.** Write
the approved list to `.ui_dev_state.md` under `## Workflows`.

---

## Step 2 — Workflow Requirements

For each workflow, write to `.ui_dev_design.md` under `## Workflow Requirements`:

- What data is displayed
- What actions the user can take
- What the empty state looks like
- What the error state looks like
- What success feedback looks like

These are not polish — they are part of the workflow. Do not start Step 3 until this section
exists on disk for the current workflow.

---

## Step 3 — Implement One Workflow at a Time

Take the next unverified workflow. Implement it completely: happy path, empty state, error
state, success feedback. Then verify it works before moving to the next one.

Verification means running the dev server and confirming the workflow completes end-to-end.
Record the result in `.ui_dev_state.md`: `pass` or `fail — <reason>`. Do not advance to the
next workflow until the current one passes.

**If you cannot verify something — a selector is unstable, you cannot trigger an error state,
you are unsure if a change took effect — stop and ask the user.** Do not guess. Do not mark
it as passed if you did not confirm it.

Repeat Step 3 for every workflow on the list.

---

## Non-Negotiables

These are binary. If any are missing, the workflow is broken. There is no workaround.

- **Searchable dropdowns for every foreign-key field.** A raw text input where the user types
  or pastes a slug/ID is not a UI. A static select is wrong if the list grows beyond ~10
  items. Use a combobox populated from live data.
- **Inline validation errors.** Errors not shown in the form where they occurred do not exist
  from the user's perspective.
- **Immediate list refresh after mutation.** A list that requires manual reload is broken.
- **Confirmation before destructive actions.** Delete/archive on first click is broken.
- **Empty states.** A blank panel with no guidance is broken.
- **Loading states.** A blank panel during fetch is broken.
- **All backend fields exposed.** If the backend accepts 8 fields and the form shows 4, the
  form is incomplete. Group secondary fields in a collapsible section if needed.
- **Dark mode by default.** Light mode is optional. Dark is not.

If you catch yourself writing "the user can work around this by..." — stop. Fix it.

---

## Design Principles

Apply these throughout. Each violation is at minimum a P1.

- **Build for the user's task, not the data model.** A page with simultaneous create forms
  for four entity types is a form dump, not a UI. Show the form for what the user is doing
  right now.
- **Propagate context.** If the user selected an epic, the create-task form knows which epic.
  Never ask the user to type what the system already knows.
- **Progressive disclosure.** Create actions behind buttons, not always-visible forms.
  Advanced fields in collapsible sections. Show the right thing at the right time.
- **Consistent interaction patterns.** If tasks use a side panel for editing, epics use a
  side panel for editing. Do not mix modals, inline forms, and dedicated pages for equivalent
  actions across sections.
- **One navigation path per destination.** Duplicate menus offering overlapping options is an
  automatic failure.
- **Linked entities visible inline.** Issues on a task are visible on the task detail view,
  not only accessible by navigating to a separate Issues section.

---

## Rules

- Check `.ui_dev_state.md` first, always. If it exists, resume. Do not restart.
- Never start coding before the workflow list exists on disk (from analysis report or user
  approval).
- Never move to the next workflow before the current one is verified.
- Empty and error states are part of every workflow, not polish.
- Follow whatever stack is already in use. For greenfield, ask the user.
- Framework agnostic. Use the frontend-design skill for visual styling guidance.
- "Mostly working" is not working. A workflow that requires copy/pasting IDs or manually
  syncing state between sections is broken.