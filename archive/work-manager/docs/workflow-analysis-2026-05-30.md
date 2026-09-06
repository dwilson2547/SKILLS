# Workflow Analysis — Work Manager
**Date:** 2026-05-30
**Verdict:** ❌ FAILS BASELINE — Multiple P0 blockers across every workflow category

---

## Summary

This UI is not usable as a project management system. The core entity hierarchy (Project →
Epic → Task → Subtask) cannot be traversed or edited without constant friction: create forms
silently omit fields the backend accepts, clicking any tree item has unpredictable side
effects (tree collapses, panel appears elsewhere, no visual confirmation of selection), and
subtasks have no detail panel at all — clicking one is a no-op from the user's perspective.
Cross-entity linking is uniformly broken: linking an issue to a task, a runbook to an issue,
or a design doc to an epic all require the user to manually copy and type raw slugs or
internal numeric IDs. The Brief Viewer is inaccessible without already knowing and typing the
exact task slug from memory. Context snapshots — a first-class field on tasks — have no UI
surface. Archive and delete operations are missing for projects, epics, tasks, subtasks,
design docs, and runbooks. The tab order is not set. The queue section sends the user to a
completely different section to view the task it surfaces. Every area of the system has at
least one P0 failure.

---

## Baseline Checklist Results

| # | Criterion | Result | Notes |
|---|-----------|--------|-------|
| 1 | All create/edit forms expose every backend field | ❌ FAIL | 17 fields missing across 6 entity forms |
| 2 | FK fields use searchable dropdowns, not raw text inputs | ❌ FAIL | 5 FK inputs are raw text (issue→task, runbook→issues, issue→runbooks, design-doc→epic link, epic create→project) |
| 3 | Required fields visually distinguished | ❌ FAIL | No asterisk, color, or label distinction anywhere |
| 4 | Validation errors surface inline | ⚠️ PARTIAL | Top-level error banner exists; field-level inline errors absent |
| 5 | Clicking an item gives obvious immediate feedback | ❌ FAIL | Tree items collapse on click; detail panel appears far below the fold with no scroll or announcement |
| 6 | Selected item always visible | ❌ FAIL | Selected state lost when navigating between sections |
| 7 | Breadcrumbs or hierarchy context indicators | ❌ FAIL | None. No indication of where the user is in Project→Epic→Task→Subtask |
| 8 | Panels can be closed/dismissed | ❌ FAIL | No close/dismiss button on any detail panel |
| 9 | Every entity CRUD-able without leaving the section | ❌ FAIL | No archive/delete for projects, epics, tasks, subtasks, design docs, runbooks |
| 10 | Archive/delete require confirmation | ⚠️ PARTIAL | Notes archive and issue resolve have confirms; everything else has no action at all |
| 11 | Lists refresh immediately after mutation | ✅ PASS | Mutations trigger refreshProjects()/fetchX() |
| 12 | Linked entities visible inline on parent record | ⚠️ PARTIAL | Task→issues shown inline. Epic→design docs shown inline. No inline view for anything else. |
| 13 | Creating a linked entity pre-populates parent ref | ❌ FAIL | Issue create form requires manually typing task_slug; no pre-population from task context |
| 14 | Cross-section filters respect context | ❌ FAIL | Brief Viewer requires typing slug manually; Issues section shows all issues with no task context |
| 15 | All elements reachable by keyboard | ❌ FAIL | No tabindex set; no Escape-to-dismiss; sidebar dropdowns not keyboard navigable |
| 16 | Enter submits forms | ⚠️ PARTIAL | Notes and criteria inputs have @keydown.enter; create forms do not |
| 17 | Focus managed on panel open/close | ❌ FAIL | No focus management anywhere |
| 18 | One navigation pattern per destination type | ❌ FAIL | Queue section navigates user to Projects section on click — two ways to reach task detail |
| 19 | Settings/global controls in one place | ✅ PASS | No settings system exists yet; not a failure |
| 20 | Filters persist within a session | ❌ FAIL | Issue/runbook filters are state but reset is untested; no persistence guarantee on section switch |
| 21 | Brief Viewer has its own filter controls | ❌ FAIL | Sidebar input requires user to type task slug manually |
| 22 | Every list has an empty state | ✅ PASS | All lists have empty-list or empty-state elements |
| 23 | API errors surface as visible feedback | ✅ PASS | Error banner present and wired |
| 24 | Loading states exist | ❌ FAIL | No loading spinners or skeleton states; panels flash blank while loading |

**Baseline score: 5 pass, 4 partial, 15 fail**

---

## Entity + Relationship Coverage

### Fields missing from create forms

| Entity | Backend accepts (create) | UI form exposes | Missing from create form |
|--------|--------------------------|-----------------|--------------------------|
| Project | title, goal, description, status, tags, blocked_reason | title, goal, description | **status, tags, blocked_reason** |
| Epic | title, description, status, tags, blocked_reason | title, description | **status, tags, blocked_reason** |
| Task | title, description, status, tags, assignee, estimated_effort, context_snapshot, blocked_reason | title, description, assignee, estimated_effort | **status, tags, context_snapshot, blocked_reason** |
| Subtask | title, description, status, tags, blocked_reason | title, description | **status, tags, blocked_reason** |
| Issue | title, severity, status, tags, task_slug, linked_runbook_ids, triage_steps, root_cause, resolution, lessons_learned | title, severity, task_slug, triage_steps, root_cause, resolution, lessons_learned | **status, tags, linked_runbook_ids** |
| Runbook | title, service, category, version, status, tags, symptoms, prerequisites, steps, verification, escalation, linked_issue_ids | title, service, category, status, symptoms, prerequisites, steps, verification, escalation, linked_issue_ids | **version, tags** |

### Fields missing from edit forms

| Entity | Missing from edit form |
|--------|------------------------|
| Project | title (edit panel has goal/description/tags but not title edit — title shown read-only in header) |
| Epic | (acceptable — title in header is read-only; would benefit from inline edit) |
| Task | context_snapshot field |
| Subtask | **entire detail/edit panel is absent** — clicking a subtask does nothing |
| Issue | tags, linked_runbook_ids |
| Runbook | version, tags |

### Entities with no archive/delete in UI

All of: Project, Epic, Task, Subtask, DesignDoc, Runbook
(Notes have archive; Issues have resolve — but no archive or delete)

### Relationships missing from UI

| Relationship | Backend supports | UI behavior |
|---|---|---|
| Issue → Task | `task_slug` FK | Raw text input — user must know the slug |
| Issue → Runbooks | `linked_runbook_ids` JSON list | Not exposed in issue form at all |
| Runbook → Issues | `linked_issue_ids` JSON list | Raw comma-separated numeric IDs — user must know internal DB IDs |
| Epic → Design Doc | many-to-many via epic_design_docs | Linking requires typing epic slug; creating a design doc uses raw epic slug text field |
| Subtask → (all) | AcceptanceCriteria, DoD, TestingLayer, Dependency endpoints exist at `/subtasks/{slug}/...` | No UI for any of these on subtasks |
| Task/Subtask → Dependencies | ItemDependency model and presumably endpoints | No UI for dependencies anywhere |
| Design Doc ← remove link from Epic | No UI | No way to unlink a design doc from an epic |
| Note ← unarchive | `/notes/{slug}/unarchive` exists | No UI |

---

## Workflow Coverage by Persona

### Creator — Sets up project structure, writes specs

| Workflow | Status | What's broken |
|---|---|---|
| Create a project with all fields | ❌ Broken | Missing status, tags, blocked_reason from create form |
| Create an epic under a project | ❌ Broken | project_slug is a raw text field; missing status, tags, blocked_reason |
| Create a task under an epic | ❌ Broken | epic_slug is a raw text field; missing status, tags, context_snapshot, blocked_reason |
| Create a subtask under a task | ❌ Broken | task_slug is a raw text field; missing status, tags, blocked_reason |
| Set a task's context snapshot | ❌ Broken | Field does not exist in UI at all |
| Link a design doc to an epic | ❌ Broken | Requires knowing/typing the epic slug; separate "Link to Epic" panel is a second create-then-link workflow |
| Edit project title | ⚠️ Degraded | Title shows in header but is not editable — only goal/description/tags are editable |
| Archive a completed project/epic/task | ❌ Broken | No archive action exists for any of these |
| View what depends on what | ❌ Broken | ItemDependency has no UI |

### Worker — Picks up tasks, records progress, logs issues

| Workflow | Status | What's broken |
|---|---|---|
| Find my next task | ⚠️ Degraded | Queue section exists but clicking a task navigates to Projects section, losing queue context |
| Open a task and understand what needs doing | ⚠️ Degraded | Brief Viewer is separate section requiring manual slug entry — no direct link from task detail |
| Update task status | ✅ Works | Status dropdown in task detail saves correctly |
| Log an issue encountered during a task | ❌ Broken | Must navigate to Issues section, then manually type the task slug — no "Log issue for this task" action on task detail |
| Complete subtask work | ❌ Broken | Clicking a subtask in the tree does nothing — no detail panel, no way to update status, add criteria, or mark done |
| Record task context/findings | ❌ Broken | context_snapshot field has no UI |
| Mark acceptance criteria verified | ✅ Works | Checkbox toggles work on task detail |
| Add testing layer results | ✅ Works | Layer status dropdowns work |
| Mark task complete | ✅ Works | Status dropdown → complete works |

### Reviewer — Checks status, reviews output, closes items

| Workflow | Status | What's broken |
|---|---|---|
| See all open issues for a specific task | ⚠️ Degraded | Visible in task detail only if you know to look there; Issues section shows all with no task filter |
| View a task brief for review | ❌ Broken | Must navigate to Brief Viewer, manually type or remember task slug |
| Resolve an issue | ✅ Works | Resolve button + confirm dialog works |
| Archive an issue that was incorrectly filed | ❌ Broken | No archive action on issues |
| Mark a runbook as validated | ✅ Works | Validate button works |
| Filter issues by severity + status | ✅ Works | Sidebar filters work |
| Navigate from issue back to linked task | ❌ Broken | Issue detail shows `task_slug` text but it is not a link or button — cannot navigate to the task |
| Navigate from runbook to linked issues | ❌ Broken | linked_issue_ids stored as raw numbers — no clickable references |

### Observer — Monitors system state, reads project briefs

| Workflow | Status | What's broken |
|---|---|---|
| See all projects and their status at a glance | ⚠️ Degraded | Project tree shows slugs and status badges but no summary metrics |
| Find a specific task's brief | ❌ Broken | Must know task slug, navigate to Brief Viewer, type it in — no search, no autocomplete |
| Search notes by tag | ✅ Works | Tag chip cloud works |
| Search notes semantically | ✅ Works | Semantic mode works |
| Browse design docs | ✅ Works | Doc list and content view work |

---

## Anti-Pattern Audit

### Form anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **Partial forms** — status, tags, blocked_reason absent from all create forms | All 4 create forms in Projects section | P0 |
| **Raw FK inputs** — epic slug typed manually to create a task | Create Task: `epic_slug` text input | P0 |
| **Raw FK inputs** — project slug typed manually to create an epic | Create Epic: `project_slug` text input | P0 |
| **Raw FK inputs** — task slug typed manually to create/link an issue | Issue form: `task_slug` text input | P0 |
| **Raw FK inputs** — epic slug typed manually to link a design doc | Design Doc "Link to Epic" form | P0 |
| **Raw ID inputs** — runbook linked_issue_ids as comma-separated DB integers | Runbook form | P0 |
| **context_snapshot field absent** from task create and edit | Create Task, task detail edit | P0 |
| **No required field indicators** | All forms | P1 |
| **Issue tags field absent** from issue form | Issue create/edit | P1 |
| **Issue linked_runbook_ids absent** from issue form | Issue create/edit | P1 |
| **Runbook tags and version absent** from form | Runbook create/edit | P1 |

### Navigation anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **Silent tree collapse** — clicking project or epic collapses children AND sets selection; user expects a selection, gets a collapse | Projects sidebar tree | P0 |
| **Subtask click is a no-op** — no detail panel exists for subtasks | Projects sidebar tree | P0 |
| **Queue navigates away** — clicking a task in Queue teleports user to Projects section | Queue section | P1 |
| **No close/dismiss** on detail panels | Project, Epic, Task detail panels | P1 |
| **No breadcrumbs** — no indication of hierarchy position | All sections | P1 |
| **Detail panel appears off-screen** — panel renders below the create form grid; user may not see it after clicking | Projects section | P1 |
| **Brief Viewer has no link from task detail** — "View Brief" button exists but Brief Viewer sidebar requires re-entering slug | Briefs section | P1 |

### Cross-entity anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **No inline issue creation from task** — must leave task, go to Issues section, type slug | Task detail | P0 |
| **Issues section has no task filter** — shows all issues; no way to scope by project/epic/task | Issues section | P1 |
| **Cannot navigate from issue to its task** — task_slug is displayed as inert text | Issue edit form | P1 |
| **Cannot navigate from runbook to linked issues** — IDs stored but not rendered as links | Runbook form | P1 |
| **Subtask has no linked criteria/DoD/testing** — backend supports these at subtask level, UI has nothing | Subtask (no detail panel) | P0 |
| **Design doc unlink not possible** — no way to remove a design doc from an epic | Epic detail panel | P1 |
| **Note unarchive has no UI** — endpoint exists, button absent | Notes section | P2 |

### List and filter anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **Brief Viewer driven by manually entered slug** — no autocomplete, no list, no search | Briefs section sidebar | P0 |
| **No task filter in Issues section** — filter by status/severity only, not by task/epic/project | Issues sidebar | P1 |
| **Design docs list has no search or filter** — will grow unbounded | Design Docs sidebar | P2 |
| **Tool Docs list has no search or filter** | Tool Docs sidebar | P2 |

### State and feedback anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **No loading states** — panels are blank while API calls run | All panels | P1 |
| **No success feedback on status dropdown changes** — project/epic/task status updates fire silently (no toast) | Project/Epic detail status dropdowns | P1 |
| **Test task cannot be archived** — dev/test data permanently occupies Queue | Tasks (no archive) | P0 |

### Keyboard and accessibility anti-patterns

| Anti-pattern | Location | Severity |
|---|---|---|
| **No tabindex** — tab order follows DOM order only; sidebar and main content not tab-indexed | Site-wide | P1 |
| **No Escape-to-dismiss** — panels and error banner not dismissable by keyboard | Site-wide | P1 |
| **Create forms don't submit on Enter** — only notes/criteria fields have @keydown.enter | All create forms | P1 |
| **No focus management** — opening a detail panel does not move focus into it | Site-wide | P1 |

---

## Prioritized Gap List

### P0 — Workflow Blockers

1. **Subtask detail panel is absent.** Clicking a subtask in the tree sets state but renders nothing. The user cannot view, edit, update status, or add acceptance criteria/DoD/testing to subtasks. A subtask is the smallest unit of work in the system and it is completely inaccessible.

2. **Task archive is absent.** There is no way to archive or close a task. Dev/test tasks created during setup permanently occupy the queue. No project lifecycle operation completes without this.

3. **Project, epic, task, subtask archive is absent.** No entity below Note has an archive action. Completed work accumulates forever with no way to tuck it out of active views.

4. **Create forms omit critical fields.** Project create is missing `status`, `tags`, `blocked_reason`. Epic create is missing `status`, `tags`, `blocked_reason`. Task create is missing `status`, `tags`, `context_snapshot`, `blocked_reason`. Subtask create is missing `status`, `tags`, `blocked_reason`. Every new entity is created with degraded data.

5. **Task context_snapshot has no UI.** This field stores the agent context snapshot for a task — a primary use-case of the system. It is present in both create and update schemas and absent from all UI forms.

6. **All FK fields are raw text inputs.** Creating an epic requires typing a project slug from memory. Creating a task requires typing an epic slug. Creating a subtask requires typing a task slug. Linking an issue to a task requires typing the task slug. Linking a design doc to an epic requires typing the epic slug. There is no dropdown, autocomplete, or picker anywhere. A user who does not already know the exact slugs cannot use the system without constantly jumping between sections.

7. **Logging an issue against a task requires leaving the task.** There is no "log issue" action on the task detail panel. The user must navigate to Issues, where the task_slug field is a blank raw text input. The task context is completely lost.

8. **Brief Viewer requires manually entering a task slug.** There is no search, no list, no autocomplete. The user must already know and type the exact slug. A Brief Viewer that requires the user to have memorized the thing they're trying to look up is not a viewer.

9. **Tree item clicks have conflicting side effects.** Clicking a project or epic simultaneously collapses the tree children AND triggers a detail panel load. The user cannot tell if they selected the item or accidentally collapsed it. Selection and expand/collapse must be separated into distinct interactions.

### P1 — High Friction

10. **Status dropdown changes on project/epic fire silently.** No toast confirmation. User cannot tell if the change saved.

11. **Detail panels have no dismiss/close action.** Once a project/epic/task detail panel is open, there is no way to close it without selecting a different item or refreshing the page.

12. **Queue task click navigates to Projects section.** The user selected a task from the Queue section and is now in a completely different section. They cannot return to the queue without losing their task selection. The queue and the task detail should coexist.

13. **Issues section has no task/epic/project scoping filter.** All issues are shown in one undifferentiated list. When a system has hundreds of issues, finding those relevant to the current task requires either remembering the slug or scrolling through everything.

14. **Cannot navigate from an issue to its linked task.** The task_slug field is displayed as static text. Clicking it does nothing. A cross-reference that is not interactive is useless.

15. **No loading states.** When the user clicks a task, the detail panel is blank for a moment while data loads. There is no spinner or skeleton. The user cannot distinguish "loading" from "this item has no data."

16. **Design doc unlink not possible.** Once a design doc is linked to an epic, it cannot be removed. Mistakes are permanent.

17. **Runbook linked_issue_ids and issue linked_runbook_ids use raw IDs.** The user must know internal database integer IDs to wire these relationships. This is worse than slug entry — at least slugs are human-readable.

18. **Issue tags and linked_runbook_ids absent from issue form.** The form is missing two fields the backend accepts.

19. **Runbook tags and version absent from form.** Version in particular matters — the system tracks versions but the user cannot set them from the UI.

20. **All create forms lack required field indicators.** The user discovers required fields by submitting and reading error messages.

21. **No tab indexing site-wide.** The site is keyboard-hostile. Every form requires a mouse to navigate.

### P2 — Polish

22. **Project title is not editable in the project detail panel.** It renders as a read-only header. Editing requires no workaround today since no one has the data yet, but this will be annoying.

23. **Design Docs and Tool Docs lists have no search or filter.** Low priority now; will become a problem at scale.

24. **Note unarchive has no UI.** The backend endpoint `/notes/{slug}/unarchive` exists but there is no button for it.

25. **Create forms do not submit on Enter.** Standard web form behavior is missing on all create forms.

26. **No focus management on panel open.** Panel appears but keyboard focus stays wherever it was.

---

## Recommendations (P0 and P1)

**1. Subtask detail panel** — Add an `x-show="selection.type === 'subtask' && subtaskDetail.subtask"` panel identical to the task detail panel. Wire `selectSubtask(slug)` to load `/subtasks/{slug}`, acceptance criteria, DoD, and testing layers. Back-populate `subtaskEditForm` on load.

**2 & 3. Archive for all work entities** — Add archive endpoints to the backend: `POST /projects/{slug}/archive`, `POST /epics/{slug}/archive`, `POST /tasks/{slug}/archive`, `POST /subtasks/{slug}/archive`. Add "Archive" buttons with confirmation dialogs to each detail panel. Archived items should be hidden from tree/queue by default with a "Show archived" toggle matching the Notes pattern.

**4. Expand all create forms** — Project: add `status` dropdown, `tags` comma input. Epic: same. Task: add `status` dropdown, `tags`, `context_snapshot` textarea. Subtask: add `status`, `tags`, `blocked_reason`. Follow the existing field-label + input pattern.

**5. context_snapshot field** — Add it to the Task edit form (large textarea, below description). Label it "Context Snapshot." Also expose it in the create form.

**6. Replace all raw FK inputs with searchable selects** — For epic_slug in Task create, project_slug in Epic create, task_slug in Subtask create, task_slug in Issue form, and epic_slug in Design Doc form: replace `<input type="text">` with a `<select>` populated from the relevant API (`GET /epics`, `GET /projects`, etc.). For the issue→task link, load tasks with a filtered `<select>` or datalist. For runbook↔issue cross-links, load slugs not numeric IDs.

**7. Inline issue creation from task** — Add a "Log Issue" button to the task detail panel that opens a pre-populated issue form (with task_slug already set) inline or in a modal. The user should never have to leave the task to log a problem with it.

**8. Brief Viewer search** — Replace the manual slug input with a searchable `<select>` or live-search input that queries `GET /tasks` and filters by title as the user types. Auto-select the currently selected task when navigating to Brief Viewer.

**9. Separate tree selection from expand/collapse** — Move expand/collapse to a caret/chevron button (`▶`/`▼`) on the left of each tree item. The tree item click area itself should only fire `selectProject`/`selectEpic`/`selectTask` — not toggle expansion. This is standard tree widget behavior.

**10. Toast on status dropdown changes** — The `updateProjectStatus`, `updateEpicStatus`, and `updateTaskStatus` methods should call `this.notify('Status updated')` on success. One line each.

**11. Dismiss buttons on detail panels** — Add an `×` button to the top-right of each detail panel that calls `selection = {}` and clears the relevant detail state.

**12. Queue section in-context task detail** — When a task is clicked in the Queue, show the task detail inline in the Queue section rather than navigating to Projects. Either embed the task detail panel in Queue or use a slide-in panel pattern.

**13. Issues task filter** — Add a task/epic/project filter to the Issues section sidebar. At minimum: add a "Task" input that drives `fetchIssues` with `&task=` param.

**14. Issue→Task navigation** — In the issue form, render the `task_slug` as a `<button class="btn-secondary btn-sm">Go to task →</button>` that calls `selectTask(issue.task_slug); activeSection = 'projects'`.

**15. Loading skeletons** — When `selectTask`, `selectEpic`, or `selectProject` is called, set a `loading: true` flag and show a simple "Loading…" placeholder in the detail panel until the API call resolves.

**16. Design doc unlink** — On the epic detail "Linked Design Docs" list, add an `× Unlink` button per doc. Wire it to `DELETE /design-docs/{doc_slug}/chunks` is wrong — this needs a dedicated unlink endpoint `DELETE /epics/{slug}/design-docs/{doc_id}`. Add that endpoint to the backend.

**17. Runbook/issue cross-links as searchable selects** — Replace `linked_issue_ids` in runbook form and `linked_runbook_ids` in issue form with multi-select components populated from live API data showing slugs and titles, not bare numeric IDs.

**18. Issue and runbook tags fields** — Add `tags` comma-input fields to both the issue form and the runbook form. Mirror the existing pattern.

**19. Version field on runbook form** — Add a `<input type="number" min="1">` for version to the runbook create/edit form.

**20. Tab indexing** — Set logical `tabindex` on all form fields and buttons. As a minimum: each section's form fields should be in sequential order, sidebar list items should be reachable. Add `@keydown.escape` handlers to close panels.
