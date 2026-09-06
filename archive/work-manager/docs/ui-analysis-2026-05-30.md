# UI Development Analysis — Work Manager
**Date:** 2026-05-30
**Workflow baseline:** `workflow-analysis-2026-05-30.md`
**Verdict:** ❌ FAILS — Broken by design, not by omission

---

## Step 0 — First Principles Reasoning

### 0a. What is this system for?

**One sentence:** A tool that lets agents and humans pick up the next unit of work, understand
what it requires, execute it, and record what was learned — structured as Projects → Epics →
Tasks → Subtasks, with notes, design docs, issues, and runbooks providing context for each
work item.

**80% hero flow:** Find the next task → read its brief → do the work → update status → log
what was encountered. This is the dominant use case. Not creating projects. Not creating
epics. Not browsing the entity hierarchy. *Executing tasks.*

**User mental state on arrival:** Focused and task-oriented. An agent or human arrives with
one question: "what do I do next, and what do I need to know?" They are not in configuration
mode. They are not building a project tree. They want to be in flow. Every second they spend
orienting themselves in the UI is friction against that.

**What should the system already know?**
- If an epic is selected, the system knows which project it belongs to.
- If a task is selected, the system knows which epic (and project) it belongs to.
- When logging an issue from a task, the system knows the task slug.
- When creating a subtask from a task detail, the system knows the task slug.
- When the user clicks "View Brief", the system knows which task is selected.

Every time the system asks the user to supply information it already has, that is a design
failure. Count how many times this happens in work-manager. Stop counting at 10.

### 0b. What would a thoughtful designer build?

**Landing surface:** The Queue — not Projects. The user who arrives to do work should land on
a view showing tasks that are ready or in-progress. This is the hero surface. It gets the
most screen real estate and is the default section on load.

**Queue surface:** A task list on the left sidebar. Clicking a task opens a full task detail
panel on the right — inline, without navigation. The panel shows: title, status (editable
inline), description, acceptance criteria (checkable), DoD, testing layers, context snapshot,
linked issues. A "Log Issue" button at the top of the task panel opens a small modal
pre-populated with the task slug.

**Brief access:** In the task detail panel, a "View Brief" button renders the markdown brief
inside the same panel — not in a different section. Alternatively, the brief is an expandable
section within the task detail itself. The user never leaves the task to read its brief.

**Projects section:** A hierarchical browser for setup and administration. Tree on the left
with expand/collapse chevrons separate from item selection. Clicking a project, epic, or task
item opens a contextual detail panel on the right. Create actions are behind "+" buttons
contextually placed adjacent to the relevant level in the tree (not four always-visible forms
on the page). The "+" button for a task appears next to the epic it belongs to; clicking it
opens a focused create modal pre-populated with the epic slug. No create form is visible by
default.

**Issues section:** A filtered list. Sidebar filter includes task, epic, and project scope —
not just status/severity. Clicking an issue shows detail with the task_slug rendered as a
clickable link that navigates to that task. Creating an issue can be done from anywhere a task
is visible via a "Log Issue" action.

**Brief Viewer:** Either eliminated as a separate section (the brief renders in the task
detail inline) or, if kept as a standalone view, it opens with a searchable task picker — a
live-search input that queries task titles and auto-selects the currently selected task if
one exists. The user never types a slug.

### 0c. Compare ideal to actual — the 30-second test

Open the app. You see: the **Projects** section with **four simultaneous create forms**
(Create Project, Create Epic, Create Task, Create Subtask) taking up the entire main panel,
plus a sidebar tree.

This is the opposite of the hero surface. The first thing the user sees is four forms for
creating entities. The dominant use case — executing work — is buried in the Queue section,
which navigates away from itself when you use it.

**This UI was designed by someone thinking about the data model, not about how the system
will be used.** There are four entity types, so there are four create forms. That logic is
correct from a DBMS perspective and completely wrong from a UX perspective.

The failure is visible in 5 seconds. That is the most important finding in this report. Every
other finding below is a consequence or a detail.

---

## Baseline Checklist — Evidence-Based

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | All create/edit forms expose every backend field | ❌ FAIL | `projectForm` has no status/tags/blocked_reason. `taskForm` has no status/tags/context_snapshot/blocked_reason. `subtaskForm` has no status/tags. 17 fields missing across 6 forms. |
| 2 | FK fields use searchable dropdowns | ❌ FAIL | `epicForm.project_slug`, `taskForm.epic_slug`, `subtaskForm.task_slug`, `issueForm.task_slug`, `designDocLink.epic_slug` are all `<input type="text">`. No `<select>`, no datalist. |
| 3 | Required fields visually distinguished | ❌ FAIL | No asterisk, color, or label distinction anywhere in the HTML. |
| 4 | Validation errors surface inline | ❌ FAIL | `handleError` sets a top-level `this.error` banner. No field-level inline errors. |
| 5 | Clicking any element gives immediate obvious feedback | ❌ FAIL | Project/epic tree clicks: simultaneously collapse children AND load detail panel. User cannot tell which happened. Subtask click: sets `selection` state, renders nothing visible. |
| 6 | Selected item always visible | ❌ FAIL | `selection` is a single shared object. Navigating sections can clear it. No persistent context indicator in the nav. |
| 7 | Breadcrumbs or hierarchy context indicators | ❌ FAIL | Zero. No indication of "you are looking at Task TASK-003 which is in Epic EPIC-001 in Project PROJ-001." |
| 8 | Panels can be closed/dismissed | ❌ FAIL | No `×` or close button on any detail panel. No `selection = {}` action wired to any dismiss control. |
| 9 | Every entity CRUD-able without leaving section | ❌ FAIL | No archive/delete endpoint or UI action for Project, Epic, Task, Subtask, DesignDoc, or Runbook. |
| 10 | Archive/delete require confirmation | ⚠️ PARTIAL | Notes use `confirm()`. Issue resolve uses `confirm()`. All other entities have no action at all. |
| 11 | Lists refresh immediately after mutation | ✅ PASS | All mutations call `refreshProjects()`/`fetchX()`. |
| 12 | Linked entities visible inline on parent | ⚠️ PARTIAL | Task shows linked issues inline. Epic shows linked design docs inline. That is all. No inline issues on subtask, no inline criteria on subtask, no inline runbooks anywhere. |
| 13 | Creating a linked entity pre-populates parent ref | ❌ FAIL | `issueForm.task_slug` is blank when opening the Issues section. `subtaskForm.task_slug` is auto-set from `selectTask` but is still a raw text input the user can see and must not accidentally clear. |
| 14 | Cross-section filters respect context | ❌ FAIL | Brief Viewer requires the user to type a slug (`briefLookupSlug`). Issues section `fetchIssues()` has no task/epic context from the Projects section. |
| 15 | All elements reachable by keyboard | ❌ FAIL | No `tabindex` set anywhere. Sidebar tree, filter controls, and detail panels all follow document order, which is not a logical tab path for this layout. |
| 16 | Enter submits forms | ⚠️ PARTIAL | `@keydown.enter` wired on `newCriterion` and `newTestingLayer.description`. No `@keydown.enter` on any create form (projectForm, epicForm, taskForm, subtaskForm). |
| 17 | Focus managed on panel open/close | ❌ FAIL | No focus management anywhere. No `$nextTick(() => this.$el.focus())` patterns. |
| 18 | One navigation pattern per destination | ❌ FAIL | Queue `@click` fires `selectTask(t.slug); activeSection='projects'` — clicking a task in Queue teleports the user to the Projects section. Two ways to reach task detail (Queue click → Projects, or click task in tree), with inconsistent behavior. |
| 19 | Settings/global controls in one place | ✅ PASS | No settings system exists yet; N/A. |
| 20 | Filters persist within a session | ⚠️ PARTIAL | Filter state is stored in component data so it persists while the app runs. However, switching sections and back is untested for reset behavior, and no filter state survives a reload. |
| 21 | Brief Viewer has its own filter controls | ❌ FAIL | The sidebar for the Briefs section is `<input type="text" x-model="briefLookupSlug" placeholder="TASK-001">` + a "Load brief" button. The user must type the exact slug. |
| 22 | Every list has an empty state | ✅ PASS | All lists have `empty-list` or `empty-state` elements. |
| 23 | API errors surface as visible feedback | ✅ PASS | `handleError` sets `this.error` shown in the top banner. |
| 24 | Loading states exist | ❌ FAIL | No loading flag checked anywhere before rendering panels. `taskDetail.task = null` is cleared at the top of `selectTask` but no loading placeholder is shown — the panel goes blank, then appears. |

**Score: 5 pass, 4 partial, 15 fail. Same as workflow analysis. Nothing has improved in the functional correctness dimension.**

---

## UX Design Quality Analysis

### Information Architecture — POOR (P0)

The Projects section presents **four create forms simultaneously** in a responsive grid: Create
Project, Create Epic, Create Task, Create Subtask. All four are visible at all times regardless
of what the user is doing. Below this grid, detail panels appear for the selected item.

This is a form dump. A user who has selected Task TASK-003 in the sidebar is looking at:
1. Create Project form
2. Create Epic form
3. Create Task form
4. Create Subtask form
5. Task detail panel (scrolled below the forms)

Items 1-4 are irrelevant to what they are doing. Items 1-4 exist because someone thought
"we have four entity types, so here are four forms." This is the DBMS-thinker failure mode
described in the skill. It passed the functional requirement (each entity can be created)
while failing the design requirement (each entity can be created *in the right context at the
right time without navigating away from your current work*).

**Specific failures:**
- The Create Project form is visible while viewing a task. These have nothing to do with each other.
- The Create Task form has an `epic_slug` text input that the user must fill in manually,
  even when an epic is selected in the sidebar. The `@click` handler on epic items does
  populate `taskForm.epic_slug = epic.slug`, but the form is **always visible** regardless of
  whether an epic is selected, so the field is blank 80% of the time.
- The detail panels appear **below** the create form grid. On any normal screen, clicking a
  project/epic/task in the sidebar makes the detail panel appear below the fold. The user
  must scroll down to see it. There is no visual cue that anything happened above the fold.

**The fix:** The Projects section should be a tree browser (sidebar) + contextual detail
panel (main). The detail panel shows the selected item. "+" buttons on each tree level open
focused create modals. The four always-visible forms go away entirely.

### Progressive Disclosure — POOR (P0)

Nothing in this UI is hidden until needed. Everything is always visible:
- All four create forms, always
- The "Link to Epic" panel in Design Docs section is always visible (and shows a prompt to
  "select a doc" when nothing is selected — meaning it exists as a blank form half the time)
- The issue form takes the full main panel width for both create and edit — the same layout
  for both modes with no distinction

Context is not propagated. The system knows which epic is selected; the "Create Task" form
does not use that knowledge unless the user has just clicked an epic in the current session.
If the user refreshes or navigates away, the pre-population is lost. There is no persistent
context propagation.

The one exception — `taskForm.epic_slug` gets populated on epic click, `epicForm.project_slug`
gets populated on project click — is a workaround for the real fix (the create button should
be contextual and the form pre-populated from the current selection, not from a side effect of
clicking a tree item).

### Interaction Model Fit — POOR (P0)

| Action | What was built | What should have been built |
|--------|---------------|----------------------------|
| Create Project (rarely done) | Always-visible form on the main panel | "New Project" button that opens a focused modal |
| Create Epic under a project | Always-visible form with raw project_slug text input | "+" button next to project in tree, modal pre-populated with project slug |
| Create Task under an epic | Always-visible form with raw epic_slug text input | "+" button next to epic in tree, modal pre-populated with epic slug |
| Create Subtask under a task | Always-visible form with raw task_slug text input | "+" button next to task in tree, or inline form at bottom of task detail panel |
| View task detail | Click task in tree → scroll past four create forms | Click task → detail panel opens on the right |
| View task brief | Click task → navigate to "Brief Viewer" section → type slug | Click "View Brief" in task detail → brief renders inline or in a panel |
| Log issue for a task | Navigate to Issues section → blank form → type task slug | "Log Issue" button on task detail → modal pre-populated with task slug |
| Archive a completed task | **Not possible** | Archive button on task detail with confirmation |

Every action in the "What was built" column requires more steps, more decisions, or more
information from the user than the corresponding "What should have been built" action. This is
not a feature gap — it is a structural design problem.

### Cognitive Load — POOR (P0)

To create a task under a specific epic, the user must:
1. Find the epic in the tree and note its slug (e.g., read "EPIC-003" from the sidebar)
2. Scroll up to find the "Create Task" form (it's above the tree in the main panel)
3. Type or paste "EPIC-003" into the `epic_slug` field
4. Fill in the remaining fields
5. Submit

Step 1 requires extracting information from the UI and holding it in memory.
Step 2 requires visual navigation back to a different part of the page.
Step 3 is the system asking the user to supply information it already has.

This is two unnecessary cognitive steps and one error-prone manual transfer. And this is the
**most common create operation in the entire system** — creating a task is not rare.

Additional cognitive load failures:
- After clicking a project/epic in the tree, the user must scroll down to see if a detail
  panel appeared. There is no other indicator that the click had an effect.
- The selected item indicator (the `.selected` class on tree items) is correct visually, but
  it only shows which item is selected, not the full hierarchy context. If you are looking at
  a task detail panel, you cannot easily see which epic or project that task belongs to.
- The Queue section says "click a task to see it" but clicking navigates to Projects and the
  task is selected somewhere in a possibly-collapsed tree. The user has to find it again.

### Spatial Consistency — POOR (P0)

| Pattern | Projects section | Issues section | Notes section | Design Docs section |
|---------|-----------------|----------------|---------------|---------------------|
| Create action | Always-visible form | Always-visible form (but no separate create form — same form is used for create and edit) | Always-visible form | Always-visible form |
| Archive/close action | Missing | "Resolve" button (not archive) | "Archive" button | Missing |
| Detail view | Panel appears below create forms | Detail is loaded into the same form (create/edit combined) | Detail loaded into form | Detail loaded into form + "Chunks" panel |
| List location | Sidebar | Sidebar | Sidebar | Sidebar |

The create/edit form conflation pattern (same form, different mode) is used inconsistently:
- Notes: same form, label changes ("Create Note" / "Edit Note") ✓
- Issues: same form, label changes ✓
- Projects: **separate forms** — always-visible "Create Project" form + separate detail panel for edit ✗
- Epics: same pattern as Projects ✗

The user must re-learn how the UI works in each section because the patterns are inconsistent.
Archive exists in Notes but not Issues (which has "Resolve"). There is no archive for any
work entity (Project, Epic, Task, Subtask, DesignDoc, Runbook). A system that has archive for
notes but not tasks does not have a coherent lifecycle model.

Status dropdowns appear in the **detail panel header** for projects, epics, and tasks — but
there is no status dropdown for subtasks (no detail panel), issues (status changed via
"Resolve" action only), or runbooks (status in the edit form body, not the header).
Inconsistent placement of a frequently-used control.

---

## Critical Design Failures Summary

These are not checklist items. These are design decisions that make the system hostile to its
primary use case.

### 1. Wrong landing surface (P0 — architectural)

The app opens to Projects. The dominant use case is executing tasks. The Queue section exists
and works (poorly), but it is not the default and navigates the user away from itself when
used. The hero surface should be the Queue. The Projects section should be secondary, for
setup and structure management.

This is a single-line config change (`activeSection: 'queue'` instead of `'projects'`) plus
the work to make the queue actually functional. It is the most impactful change possible.

### 2. Four always-visible create forms (P0 — structural)

The Projects section main panel is occupied by four create forms at all times. These forms are
context-blind, partially incomplete, and take up space that should belong to the selected
item's detail panel. Remove them. Replace with "+" buttons at each tree level that open
focused create modals. Detail panel gets the full main area.

### 3. Queue navigates away from itself (P0 — behavioral)

`selectTask(t.slug); activeSection='projects'` on line 399. This is the most obviously broken
interaction in the system. The user is in the Queue. They click a task to work on it. They are
now in the Projects section, and they have to find their task again in the tree. The fix is to
show the task detail panel within the Queue section, not to teleport the user somewhere else.

### 4. Brief Viewer is a dead end (P0 — workflow)

The Brief Viewer is the most important information surface for an agent picking up a task.
Accessing it requires: navigating to the "Brief Viewer" section, typing the task slug from
memory, clicking "Load brief". This is three steps that require the user to already have the
information they are trying to look up.

The "View Brief" button on the task detail does work (it calls `loadBriefBySlug(selection.slug)`)
but it navigates to a different section rather than rendering inline. The fix is to render the
brief within the task detail panel — it does not need its own section.

### 5. Subtask is entirely inaccessible (P0 — missing feature)

Clicking a subtask in the tree calls `selection = {type:'subtask', slug: subtask.slug, task: task.slug}`.
There is no `x-show` panel in the HTML that responds to `selection.type === 'subtask'`. The
subtask is the smallest unit of work in the system. It cannot be viewed, edited, or updated
from the UI in any way. This is not a partial failure — it is a complete gap.

---

## Prioritized Findings

### P0 — Design/Structural Failures

| # | Finding | Impact |
|---|---------|--------|
| D-1 | Wrong landing surface — Projects instead of Queue | Every session starts in the wrong place |
| D-2 | Four always-visible create forms dominate the main panel | Hero surface is a form dump |
| D-3 | Queue navigates user out of Queue on task click | Queue is unusable for its primary purpose |
| D-4 | Brief Viewer is a separate section requiring manual slug entry | Agent brief lookup is broken |
| D-5 | Subtask detail panel does not exist | Subtasks are completely inaccessible |
| D-6 | Tree collapse and item selection are the same click | User cannot select without collapsing |
| D-7 | No archive for Project, Epic, Task, Subtask, DesignDoc, or Runbook | Completed work permanently occupies all views |
| D-8 | Detail panels appear below the fold (below create form grid) | User does not see the effect of clicking |
| D-9 | All FK fields are raw text inputs | User must memorize or copy/paste slugs to use the system |
| D-10 | context_snapshot field absent from all forms | Primary agent-use-case field has no UI surface |

### P0 — Functional Checklist Failures (from workflow analysis)

| # | Finding |
|---|---------|
| F-1 | No inline issue creation from task — must leave task, lose context |
| F-2 | 17 fields missing across 6 entity create forms |
| F-3 | No required field indicators anywhere |
| F-4 | No focus management on panel open/close |
| F-5 | No loading states |

### P1 — High Friction

| # | Finding |
|---|---------|
| P-1 | No breadcrumbs / hierarchy context anywhere in the UI |
| P-2 | No dismiss/close button on any detail panel |
| P-3 | Status update on project/epic fires silently (no toast) |
| P-4 | Issue task_slug is static text — not a link to the task |
| P-5 | Issues section has no task/epic/project scoping filter |
| P-6 | Design doc cannot be unlinked from an epic |
| P-7 | Runbook linked_issue_ids uses raw integer IDs, not slugs |
| P-8 | Tab order is document order — not a usable keyboard path |
| P-9 | Create forms do not submit on Enter |
| P-10 | Note unarchive endpoint exists but has no UI button |

---

## Redesign Priorities

The following represent the minimum structural changes to make this UI functional for its
primary use case. These are not incremental improvements to the current design — several
require structural changes.

**1. Make Queue the landing surface and make it self-contained.**
Change `activeSection: 'projects'` to `activeSection: 'queue'`. Remove `activeSection='projects'`
from the Queue task click handler. Add a task detail panel to the Queue section (can reuse
the same panel HTML, just conditionally show it when `activeSection === 'queue' && selection.type === 'task'`).

**2. Replace the Projects section create form grid with contextual "+" buttons.**
Remove the four always-visible create panels from the Projects section main area. The main
area becomes: empty state when nothing is selected, or the selected entity's detail panel.
Add a "+" button to each level of the tree for contextual creation. Each "+" opens a focused
modal with the parent slug pre-populated.

**3. Add subtask detail panel.**
Add `x-show="selection.type === 'subtask' && subtaskDetail.subtask"` panel. Wire a
`selectSubtask(slug)` method to load the subtask and its associated data. The panel should
match the task detail panel structure.

**4. Add archive endpoints and UI for all work entities.**
Backend: `POST /projects/{slug}/archive`, `POST /epics/{slug}/archive`,
`POST /tasks/{slug}/archive`, `POST /subtasks/{slug}/archive`.
UI: Archive button with confirmation on each detail panel. Archived items hidden by default
with a "Show archived" toggle.

**5. Replace all FK text inputs with searchable selects.**
Every raw slug/ID text input that links to another entity becomes a `<select>` populated from
live API data. At minimum: project_slug in epic create, epic_slug in task create, task_slug
in subtask create, task_slug in issue form, epic_slug in design doc link form.

**6. Add context_snapshot to task forms.**
Add a "Context Snapshot" textarea to both the task create form and the task edit section.
This is a first-class field in the data model and the primary mechanism for agents to
understand what they're doing.

**7. Fix the Brief Viewer.**
Either: render the brief inline in the task detail panel (preferred — eliminates the need for
a separate section), or: replace the manual slug input with a live-search input/select that
queries `GET /tasks` and auto-populates from the current task selection.

**8. Add inline issue creation from task detail.**
"Log Issue" button on the task detail panel opens a modal pre-populated with `task_slug`.
The user never has to leave the task to log a problem.

---

## Overall Verdict

**This UI does not meet requirements. It fails first principles, fails the baseline checklist
on 15 of 24 criteria, and fails all five UX design quality dimensions.**

The system was built entity by entity, checking boxes: "project CRUD done, epic CRUD done,
task CRUD done..." Each entity got a form and a list. The result is a database administration
interface, not a project management tool.

The central failure is structural: the UI is organized around the data model (four entity
types, four create forms, eight sections) rather than around how the system is used (pick up
work, execute it, record what happened). Until the Projects section is restructured and the
Queue becomes functional, no amount of field additions or bug fixes will make this system
usable for its intended purpose.

The good news: the backend API is solid, the data model is correct, and the Alpine.js
foundation is reasonable. The problems are entirely in the UI layer. They are fixable.
