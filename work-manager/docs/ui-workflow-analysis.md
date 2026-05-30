# Work Manager UI — Workflow Coverage Analysis

**Date:** 2026-05-30  
**Scope:** `work-manager/ui/index.html` (Alpine.js SPA, ~680 lines)  
**Method:** Static code review against API surface and design intent

---

## Summary

The UI covers the happy-path CRUD surface area reasonably well but has significant gaps in
**planning workflows**, **entity editing**, **agent-facing views**, and **cross-entity
navigation**. Many sections are write-only — you can create things but cannot fully manage
them once created.

---

## Section Coverage

### Projects (project → epic → task → subtask hierarchy)

| Workflow | Status | Notes |
|---|---|---|
| Create project | ✅ Covered | Title, goal, description |
| Create epic | ✅ Covered | Requires manual project slug entry |
| Create task | ✅ Covered | Title, description, assignee, effort |
| Create subtask | ✅ Covered | Requires manual task slug entry |
| View task detail | ✅ Covered | Criteria, testing layers, DoD, status |
| Update task status | ✅ Covered | Dropdown in task detail panel |
| Add/check acceptance criteria | ✅ Covered | Inline checklist in task detail |
| Add/update testing layers | ✅ Covered | Layer type + status selectors |
| Write/save definition of done | ✅ Covered | Textarea + save button |
| **Edit project** | ❌ Missing | Selecting a project expands the tree; no edit form |
| **Edit epic** | ❌ Missing | Selecting an epic expands its tasks; no detail panel |
| **Edit task core fields** | ❌ Missing | Title, description, assignee, effort not editable via UI |
| **Edit subtask** | ❌ Missing | Clicking subtask sets selection but shows nothing |
| **Set task blocked_reason** | ❌ Missing | Status can be set to `blocked` but no reason field |
| **Set task tags** | ❌ Missing | Tags are critical for brief note-matching but absent from create/edit |
| **Manage task dependencies** | ❌ Missing | No dependency management UI |
| **View linked issues on task** | ❌ Missing | Task detail panel doesn't show issues filed against it |
| **Epic status rollup** | ❌ Missing | No at-a-glance task progress per epic (e.g., 3/5 complete) |
| **Project status rollup** | ❌ Missing | No summary of epic completion or overall project health |

### Notes

| Workflow | Status | Notes |
|---|---|---|
| Create note with scope tag | ✅ Covered | Enforces `scope:` tag requirement |
| Edit existing note | ✅ Covered | Click to load into form, save |
| Archive note | ✅ Covered | Warning button + show-archived toggle |
| Search by tag | ✅ Covered | Tag cloud filter chips |
| Semantic search | ✅ Covered | Backend `/notes?q=` proxy |
| Text search | ⚠️ Partial | Client-side filter on loaded notes only; misses unloaded pages |

### Design Docs

| Workflow | Status | Notes |
|---|---|---|
| Create design doc | ✅ Covered | With optional epic link on create |
| Upload markdown file | ✅ Covered | File picker → textarea |
| Edit existing doc | ✅ Covered | Select → edit textarea → save |
| Link doc to (additional) epic | ✅ Covered | Right panel after selecting a doc |
| View doc chunks (for brief context) | ✅ Covered | Chunk cards shown in right panel |
| **Rendered markdown preview** | ❌ Missing | Content is plain textarea; no preview toggle |
| **View which epics a doc is linked to** | ❌ Missing | No display of existing epic links |

### Issues

| Workflow | Status | Notes |
|---|---|---|
| Create issue | ✅ Covered | Full form including triage/root cause/resolution/lessons |
| Edit issue | ✅ Covered | Click to load, save |
| Resolve issue | ✅ Covered | Warning-style button |
| Filter by status / severity | ✅ Covered | Two select dropdowns in sidebar |
| **Confirm before resolve** | ❌ Missing | One-click resolve with no confirmation |
| **Archive issue** | ❌ Missing | Only resolve; no archival path |

### Runbooks

| Workflow | Status | Notes |
|---|---|---|
| Create runbook | ✅ Covered | Full form |
| Edit runbook | ✅ Covered | Click to load, save |
| Validate runbook | ✅ Covered | One-click validate |
| Filter by service / category / status | ✅ Covered | Sidebar filters |
| **Link to issues by slug** | ⚠️ Partial | Links by internal numeric ID via comma-separated text field; no slug lookup |

### Brief Viewer

| Workflow | Status | Notes |
|---|---|---|
| Load brief by task slug | ✅ Covered | Manual slug input in sidebar |
| View rendered markdown brief | ✅ Covered | `marked.parse()` → innerHTML |
| View completion blockers | ✅ Covered | Red danger box at top |
| **Load brief from task selection** | ⚠️ Partial | "View Brief" button in task detail switches to Briefs section but brief is also shown inline in Projects — two parallel paths, potentially confusing |

---

## Missing Sections

### Tool Docs (entirely absent)

The API has a full `/tool-docs` router with source management, indexing, and semantic search
(`GET /tool-docs/search`). There is no section in the UI for this. Users cannot:
- View indexed tool doc sources
- Trigger a manual reindex
- Search tool documentation
- Add or remove tool doc repos

### Work Queue / "Next Task" View (entirely absent)

The CLI exposes `workman next` which returns the highest-priority ready task. The UI has no
equivalent planning view. A key human workflow — "what should I work on?" — requires going
to the CLI or manually scanning the project tree.

Proposed view: a filtered list of all `ready` tasks across projects, ordered by priority, with
quick-access "Start" button (sets `in_progress`).

### Import / Export (entirely absent)

The API has `GET /*/export` and `POST /*/import` for all entity types, and the CLI exposes
`workman export` and `workman import`. The UI has no equivalent. Users cannot:
- Back up or migrate data via the browser
- Bulk-import design docs or notes

---

## UX / Navigation Issues

### 1. Epic and project nodes are expand-only

Clicking a project or epic in the tree expands its children and sets `selection`, but the
main panel has no handler for `selection.type === 'project'` or `selection.type === 'epic'`.
The right-hand panel stays empty (only the create forms are shown). Users cannot view or
edit any epic-level fields (description, status, tags, linked design docs).

### 2. Brief viewer duplication

A rendered brief appears both in the Projects section (after selecting a task and calling
`loadBriefBySlug`) AND in the dedicated Briefs section. The "View Brief" button in the task
detail panel navigates away from Projects to Briefs, but the brief was already loading
inline. This is confusing — the dual-path should be resolved to one canonical location.

### 3. Slug entry for parent references

Creating an epic requires manually typing `PROJECT-001`. Creating a task requires typing
`EPIC-001`. Creating a subtask requires typing `TASK-001`. These are error-prone when the
tree is already visible — parent slug should auto-populate from the current selection.

### 4. No confirmation on destructive actions

Archive note, resolve issue — both are one-click with no confirmation. At minimum a confirm
dialog should guard these.

### 5. Text search is client-side only

Note text search filters the already-loaded list. If there are many notes and the API
paginates in the future this will silently miss results. All search should go through the
backend.

### 6. Toast duration and error clearing

Errors set in `this.error` via `handleError()` stay visible until the user dismisses them.
Toasts auto-dismiss in 2500 ms. Errors that look like API validation messages should also
auto-dismiss (or be styled differently from persistent system errors).

---

## Prioritized Gap List

**P0 — Workflow blockers** (things you cannot do at all in the UI):
1. Edit an existing task's core fields (title, description, assignee, effort, tags)
2. View/edit an epic (description, status, tags, linked design docs)
3. Set task tags (critical for brief note-matching — notes won't be pulled into briefs)
4. Set blocked_reason when marking a task blocked
5. Tool Docs section (no visibility into indexed doc repos or search)

**P1 — Significant workflow friction**:
6. Auto-populate parent slug from tree selection when clicking a create panel
7. Work queue / "next task" view — ready tasks across all projects
8. View issues linked to a task (in the task detail panel)
9. Rendered markdown preview for design docs
10. Confirm dialogs for archive/resolve

**P2 — Nice to have**:
11. Epic-level task progress rollup (X/Y tasks complete)
12. Import/export UI
13. View which epics a design doc is already linked to
14. Fix note text search to go through backend
15. Collapse the dual brief-viewer paths to one

---

## Notes for Implementation Planning

- **Task tags** is the single highest-leverage fix: without tags on tasks, note-pulling in
  briefs won't work, which undermines the core agent-briefing value proposition.
- **Epic detail panel** would unlock a large surface area with one component: epics already
  have status, description, and design-doc links in the API.
- **Parent slug auto-populate** is a small change with high daily impact — when a task is
  selected, the create-subtask form's `task_slug` should pre-fill.
- The **Briefs section** should be the single canonical brief view; the inline version in
  Projects should be removed or collapsed to just a "View Brief" button.
