# UI Analysis — Work Manager (New UI, index.html)
**Date:** 2026-05-30
**Analyst:** UI Development Skill (First Principles + Baseline Checklist)
**Previous analysis:** ui-analysis-2026-05-30.md (old index_old.html — 5/4/15 pass/partial/fail)

---

## Step 0 — First Principles

### 0a — What is this system for?

This is a tool that lets agents and humans pick up the next unit of work, execute it,
and record what they discovered — with tasks, design docs, issues, and runbooks all
in one place so nothing has to be looked up elsewhere.

**Primary use 80% of the time:** Find the next task. Open it. Work it. Update status.
Log what went wrong.

**User mental state:** Focused. Task-oriented. Wants minimum friction to context-switch
from thinking to doing.

**What decisions should the system make for the user?** If I'm in a task, it knows
the task slug. It should never ask me to type it. If I'm in an epic, it knows the epic
slug and the parent project.

### 0b — Ideal experience

Landing surface: **Queue**. Active tasks in a scrollable sidebar. First (or most urgent)
task auto-highlighted. Full detail panel to the right — title, status, description,
acceptance criteria, and DoD visible without expanding anything. Log Issue and Subtasks
one click. Brief behind an accordion (load on demand — expensive operation).

What's hidden: anything that isn't the current task. Create forms, other sections,
sibling tasks, testing layers — secondary or behind accordions.

### 0c — Actual vs ideal (30-second test)

**Landing section is Queue. First task is auto-selected with full detail.**

This is correct. The hero flow is working. The headline failure of the old UI
(opening to a DBMS admin panel with 4 create forms) is fixed.

The gaps now are not structural failures — they are completeness gaps in specific
entity edit panels and a few subtle behavioral issues. The foundations are sound.

---

## Baseline Checklist Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | All create/edit forms expose every backend field | ❌ FAIL | Tool Docs: no edit form. Issues: missing status, triage_steps, root_cause, resolution, lessons_learned. Runbooks: missing service, category, version, symptoms, prerequisites, verification, escalation. |
| 2 | FK fields use searchable dropdowns from live data | ✅ PASS | All FK inputs use `<datalist>` populated from live allProjects/allEpics/allTasks/allRunbooks/allIssues |
| 3 | Required fields visually distinguished | ✅ PASS | `.required::after { content: " *"; color: red; }` applied via CSS class on labels |
| 4 | Validation errors surface inline | ✅ PASS | Notes scope: tag enforced inline with `noteInlineError` / `modalForm.scopeError`. Top-level error banner on API failures. |
| 5 | Clicking an item gives immediate obvious feedback | ✅ PASS | `.active` class on list items, detail loads into main panel |
| 6 | Selected item always visible without memory | ✅ PASS | Active styles on sidebar items; breadcrumbs in detail panel |
| 7 | Breadcrumbs or hierarchy context | ✅ PASS | All detail panels have breadcrumb row with clickable navigation back to parent |
| 8 | Panels can be closed/dismissed | ✅ PASS | "Clear" button on all detail panels. Modal: "Close" button + Escape key + click-outside |
| 9 | Every entity CRUD without leaving section | ⚠️ PARTIAL | Tool Docs: no edit, no archive. Design Docs: no archive. Issues: no delete (resolve-only). Runbooks: no archive/delete. |
| 10 | Archive/delete require confirmation | ✅ PASS | `confirm()` on all archive actions; delete criterion/layer have confirms |
| 11 | Lists refresh immediately after mutation | ✅ PASS | All mutations await refreshProjects()/loadQueue()/loadX() before returning |
| 12 | Linked entities visible inline on parent record | ✅ PASS | Issues inline on task. Design docs inline on epic. Linked runbooks inline on issue. |
| 13 | Creating linked entity pre-populates parent ref | ✅ PASS | `openModal('issue', { task_slug: selectedTask.slug })` pre-fills task_slug |
| 14 | Filtering/searching respects context | ✅ PASS | Issues section has task-slug datalist filter. Brief is now inline in task (no standalone viewer) |
| 15 | All elements reachable by keyboard | ⚠️ PARTIAL | Escape closes modal ✅. Modal first input auto-focused ✅. Form `@submit.prevent` on modal ✅. No tabindex attribute management; focus not restored to trigger on modal close. |
| 16 | Forms can be submitted with Enter | ✅ PASS | Modal form uses `@submit.prevent="submitModal()"` — Enter submits. Inline add-forms use button clicks (acceptable). |
| 17 | Focus managed on panel open/close | ⚠️ PARTIAL | Modal open: `$refs.modalFirst?.focus()` ✅. Modal close: no focus restoration to trigger button. Panel open/close: no focus management. |
| 18 | One and only one navigation pattern per destination | ✅ PASS | Single top nav bar. Breadcrumbs navigate within hierarchy. No duplicate menus. |
| 19 | Settings/global controls in one place | ✅ PASS | No settings system yet; not a failure. |
| 20 | Filters persist within a session | ✅ PASS | `queueFilter`, `noteFilter`, `noteTagFilter`, `issueFilter`, `runbookFilter` are stateful; preserved on section switch and back. |
| 21 | Brief Viewer has its own filter controls | ✅ PASS | Brief is now an inline accordion in task detail — no standalone "Brief Viewer" section. Old P0 is resolved. |
| 22 | Every list has a non-blank empty state | ✅ PASS | All sections have empty-state elements with guidance text |
| 23 | API errors surface as visible feedback | ✅ PASS | `apiError` banner rendered at top of main panel. `showToast()` on every error. |
| 24 | Loading states exist | ✅ PASS | `loadingList` shows "Loading…" in sidebar. `loadingDetail` shows "Loading task detail…" in main panel. |

**Baseline score: 18 pass, 3 partial, 3 fail**
**Previous score: 5 pass, 4 partial, 15 fail**

---

## Failure Details

### P0 — Blocks normal workflow completion

**F1 — Tool Docs: no edit form (P0)**
The `selectedToolDoc` panel (lines 1149–1179) is entirely read-only. Title, source_url, tags,
and description are rendered as static info cards with no inputs. The create modal accepts
all four fields. The edit path is completely absent. Any tool doc added with wrong metadata
cannot be corrected through the UI.

```
Affected entity: Tool Docs
Missing: PUT /api/tool-docs/{slug} is never called — no edit panel exists
Action required: Add edit form mirroring create modal fields
```

**F2 — Issues: missing critical operational fields in edit panel (P0)**
The issue edit panel (lines 1092–1098) exposes: title, severity, task_slug,
linked_runbook_slugs, description. Missing from the edit view:
- `status` (editable select) — cannot update from open → investigating → resolved except via the "Resolve" button which jumps straight to resolved
- `triage_steps` — operational field agents need to fill as they investigate
- `root_cause` — the primary knowledge-capture field for issues
- `resolution` — what was done to fix it
- `lessons_learned` — key output for organizational learning

These are not cosmetic. An issue with no root_cause, resolution, or lessons_learned fields
in the UI is not usable as an incident investigation tool.

```
Affected entity: Issues edit panel
Missing: status select, triage_steps textarea, root_cause textarea, resolution textarea, lessons_learned textarea
Action required: Expand issue edit grid to include all fields
```

**F3 — Runbooks: missing critical content fields in edit panel (P0)**
The runbook edit panel (lines 1128–1140) exposes: title, status, tags, linked_issue_slugs,
description, steps. Missing:
- `service` — which service this runbook applies to
- `category` — classification
- `version` — runbook version
- `symptoms` — what triggers this runbook (most important for search/discovery)
- `prerequisites` — what must be true before following it
- `verification` — how to confirm it worked
- `escalation` — what to do if it doesn't work

A runbook without symptoms and verification is half a runbook.

```
Affected entity: Runbooks edit panel
Missing: service, category, version, symptoms, prerequisites, verification, escalation
Action required: Expand runbook edit grid to include all fields
```

---

### P1 — Requires unnecessary work or creates cognitive friction

**F4 — Queue auto-selects first task on load without user action (P1)**
`loadQueue()` lines 1769–1774: if there is no selected task (or the selected one dropped
off the filtered list), it automatically calls `loadTaskDetail(queueTasks[0].slug)`. The
user arrives to the queue and sees task #1's detail already loaded without having chosen
it. The empty-state welcome panel ("Select a task from the sidebar") is never shown when
there are tasks. This is a small but real cognitive surprise — the user didn't ask for
that task; the system decided for them. Removing the auto-select lets the queue empty state
serve its purpose.

**F5 — All task detail accordions default to expanded (P1)**
`accordions` initializer (lines 1409–1417): subtasks, criteria, testing, dod, brief, issues,
siblings — all `true`. A task with 5 subtasks, 4 acceptance criteria, 3 testing layers, and 2
linked issues renders a very long page with every section visible at once. The Brief accordion
is particularly expensive — it renders a "View Brief / Hide Brief" toggle inside an already-
open accordion, requiring two clicks to actually see the brief. Recommended defaults: subtasks
open, criteria open, testing open, dod open, brief closed (expensive), issues open, siblings
closed.

**F6 — Issue linked-runbooks panel shows slugs, not titles (P1)**
Lines 1102–1108: `x-text="slug"` renders the raw slug (e.g., `deploy-rollback-v2`) on each
linked runbook card. `allRunbooks` is populated with both slug and title. This should show
the title with the slug as secondary context, consistent with how all other linked entities
are displayed.

**F7 — "Active" queue filter includes Draft tasks (P1)**
Lines 1757–1762: Active = in_progress + ready + draft. Draft tasks are not ready to be worked
— they haven't been reviewed or accepted. Including them in the "active" queue pushes ready
work below unfinished planning items. Active should be in_progress + ready (tasks that can be
picked up right now). Draft should remain its own filter.

**F8 — Severity on issues is a free-text input (P1)**
Lines 1094, 1296: `<input type="text" x-model="selectedIssue.severity" placeholder="high">`.
Severity is an enum (low, medium, high, critical). Allowing free text produces inconsistent
values that break sorting and filtering. Should be a `<select>` with defined options.

**F9 — Issue status only editable via "Resolve" action; no dropdown (P1)**
The toolbar has a "Resolve" button that calls `POST /api/issues/{slug}/resolve` directly —
this is a one-way transition. There is no way to set status to `investigating` or revert
from resolved back to open. A status select alongside Severity would cover the full lifecycle.

---

### P2 — Cosmetic or minor polish

**F10 — Design Docs missing archive/delete (P2)**
Design doc detail has Save and Clear but no Archive. Lower priority since it's a document
store and archival is less critical, but it creates asymmetry with Notes (which have
Archive/Unarchive). Worth adding for completeness.

**F11 — Focus not restored to trigger on modal close (P2)**
When a modal is closed, focus returns to the document body rather than the button that
opened it. Minor for mouse users; noticeable for keyboard-only users who will lose their
position in the tab order.

**F12 — Queue "All" filter has no pagination or count cap (P2)**
`GET /api/tasks` with no filter returns all tasks. For a large project this list is
potentially unbounded. No truncation or pagination is in place. At scale this becomes P1,
but for current project sizes it's P2.

**F13 — Project edit missing tags and goal fields (P2)**
Project detail panel (lines 682–694) exposes: title, status, description. The backend likely
accepts tags, goal, and blocked_reason on projects based on pattern with epics. Lower priority
since projects are created infrequently, but the edit form should match the full schema.

---

## UX Design Quality

### Information architecture — GOOD
Each surface shows contextually relevant content. Queue shows tasks. Task detail shows task
context. No form dumps. No unrelated content competing for visual weight. Hero surface is
task execution, as it should be.

### Progressive disclosure — ACCEPTABLE with caveats
Create forms are behind + buttons (correct). Accordions for complex task sections (correct).
However: all accordions default open (F5). A task with full metadata renders an overwhelming
amount of content at once. The Brief accordion in particular should be closed by default — it
adds a "View Brief / Hide Brief" toggle inside an already-open panel, creating a nested
visibility toggle that's confusing.

### Interaction model fit — GOOD
| Entity | Pattern | Assessment |
|--------|---------|------------|
| Create any entity | Modal on + button click | ✅ Correct |
| Edit project/epic/task | Inline form in detail panel | ✅ Correct for complexity level |
| Edit subtask | Inline within accordion card | ✅ Correct for sub-entity |
| Archive | confirm() → action → list refresh | ✅ Correct |
| Resolve issue | Action button (one-way transition) | ⚠️ Should be status select (see F9) |
| Edit tool doc | None | ❌ Missing entirely (F1) |

### Cognitive load — SIGNIFICANT IMPROVEMENT
Creating a task under an epic: select epic → click + Task in toolbar → modal opens pre-scoped
to that epic → fill title → Create. Three deliberate actions, zero manual slug copying.
Previous UI required manually typing the epic slug from memory.

One regression: auto-selecting the first task on queue load (F4) removes user agency on
landing.

### Spatial consistency — GOOD
Consistent patterns throughout:
- Toolbar layout: Save [primary], action buttons [ghost], Archive [danger], Clear [ghost]
- Breadcrumbs in same position on all detail panels
- Card + accordion structure consistent across queue and projects
- Status badges use same color semantics in all sections
- Datalist pattern for FK fields consistent everywhere

Minor inconsistency: Notes have Archive/Unarchive; Design Docs, Runbooks, and Issues do not
have archive capability. Same content type (documents), different treatment.

---

## Summary Verdict

**The new UI is a meaningful improvement. The structural failure of the old UI is fixed.**
The default landing is the Queue. Create forms are behind contextual buttons. FK fields use
datalists. Breadcrumbs are present. Accordions organize complex task detail. All P0 failures
from the previous analysis are resolved at the structural level.

**What remains are completeness and correctness issues, not design failures:**
- Three edit panels are incomplete: Tool Docs (no edit), Issues (5 missing fields), Runbooks (7 missing fields)
- The "Active" filter definition is semantically wrong
- Auto-selection on queue load removes user agency
- All accordions expanded by default makes long pages overwhelming

**Recommended priority order for next iteration:**
1. F2 (Issues edit fields) — operational critical
2. F3 (Runbooks edit fields) — operational critical  
3. F1 (Tool Docs edit panel) — basic CRUD completeness
4. F7 (Active filter fix) — semantically incorrect today
5. F8/F9 (Severity select + Issue status select) — data quality
6. F5 (Accordion defaults) — UX quality
7. F4 (Queue auto-select) — user agency
8. F6 (Linked runbook titles) — polish
9. F10–F13 — polish

The system is functional for the hero flow (Queue → Task → Execute → Log Issue).
The secondary workflows (Issues, Runbooks as first-class entities) are underserved by their
edit panels.
