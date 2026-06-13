---
name: ui-repair-loop
description: >
  Repair a broken or partially functional UI by iterating through pre-determined workflows
  using Playwright MCP live browser testing. Fix failures immediately, then re-verify.
  Use when the user says a UI is broken, workflows don't work, or asks you to make a UI
  functional end-to-end. Not for building new UIs from scratch — use ui-development for that.
---

# UI Repair Loop

A UI is not repaired until every workflow the system is meant to support can be executed
end-to-end without errors, manual workarounds, or console failures. "Mostly working" is not
done. This skill is a closed loop: verify → identify failure → fix → re-verify → repeat until
clean.

---

## Prerequisites

Before starting, confirm:

1. **The UI is running.** Find the service port and verify `curl http://localhost:<port>` returns
   HTML. If it is not running, start it (check docker-compose.yml or the project README).
2. **The API is running.** Verify `curl http://localhost:<api-port>/health` or the equivalent.
   Check docker-compose.yml for port mappings. All UI → API calls will fail silently if the API
   is down.
3. **Playwright MCP is available.** Use `playwright-browser_navigate` to load the UI. If that
   tool is not available, stop and ask the user to enable the Playwright MCP before proceeding.
4. **You have the API schema.** You cannot fix API contract bugs without knowing what the
   backend actually accepts. Locate the schema files (Pydantic models, OpenAPI spec, or router
   files) before you start. Read them — do not guess field names, HTTP methods, or enum values.

---

## Step 1 — Establish the Workflow List

Read the workflow list from `.ui_dev_state.md` or `docs/workflow-analysis-*.md`. If neither
exists, derive from API routes and UI navigation — every entity with CRUD endpoints implies
a workflow, every UI section implies at least one.

Compile a flat numbered list. Each workflow should be one sentence: what the user does and
what the expected outcome is. Example:

```
1. Create a project — user fills title/goal, submits, project appears in sidebar
2. Create an epic under a project — epic_slug pre-populated, epic appears in project tree
3. Archive a task — task disappears from active queue, status set to abandoned
4. Add acceptance criterion to a task — criterion appears in list with Pending badge
5. Delete acceptance criterion — criterion removed, list updates immediately
6. View task brief — markdown brief renders inline in task detail
...
```

**Do not start testing until this list is written.** Missing workflows discovered mid-repair
are expensive. It is better to spend 5 minutes writing the list than to finish and realize
an entire section was never tested.

---

## Step 2 — Load the UI and Capture Baseline

```
playwright-browser_navigate: http://localhost:<port>
playwright-browser_console_messages (level: error)
```

Record the number of console errors on cold load. Any errors at this point are structural
failures — JS not loading, component failing to init, API calls failing on mount.
Fix these first before proceeding to workflow testing. A component that fails to init will
silently break every workflow in that section.

---

## Step 3 — Iterate Through Workflows

For each workflow in the list:

### 3a — Execute the workflow via Playwright

Use `playwright-browser_snapshot` to orient before clicking. Use `playwright-browser_click`,
`playwright-browser_fill_form`, `playwright-browser_select_option`,
`playwright-browser_handle_dialog` as needed to drive the workflow.

Do not guess at element refs. Always take a snapshot first to get stable refs for the current
page state.

### 3b — Check for errors immediately after each action

```
playwright-browser_console_messages (level: error)
```

Check after every create, save, delete, and navigation action. An API error that doesn't
surface in the UI will only show in the console. A 422 after a form submit means the payload
is wrong. A 405 means the wrong HTTP method. A 404 means the endpoint doesn't exist. Treat
all of these as failures that must be fixed before moving on.

### 3c — Verify the outcome

The outcome must be observable in the UI — not inferred. For creates, the new item must
appear in the sidebar or list. For deletes, the item must be gone. For saves, re-open the
detail and confirm the data persisted. For archive/status changes, confirm the item's state
changed in the UI.

**Do not mark a workflow as verified if you could not observe the outcome.** If the action
appeared to succeed but the list didn't update, the workflow is broken.

### 3d — If the workflow fails, fix it immediately

Do not batch failures. Fix the current workflow before moving to the next. This keeps the
scope of each fix contained and avoids cascading issues where one unfixed bug causes false
failures in later workflows.

**Commit after each successful fix-and-verify cycle.** Per-workflow commits give you rollback
granularity — a fix to workflow 9 that breaks workflow 4 can be reverted without losing
workflows 5 through 8.

---

## Step 4 — Diagnosing Failures

### API Contract Bugs (most common)

The UI was probably built against an assumed API that differs from the actual one. The most
common contract bugs are:

| Symptom | Likely cause |
|---|---|
| 405 Method Not Allowed | UI uses PUT, API only accepts PATCH |
| 422 Unprocessable Entity | Extra field in payload (`extra='forbid'`), wrong field name, or empty string where null is required |
| 404 Not Found | Endpoint doesn't exist — UI invented it |
| 400 Bad Request | Enum value not in the allowed set |
| Silent failure, no toast | Missing `async`/`await` on the function, or error swallowed |

**How to diagnose 422s:**
1. Check the browser console for the response body — most APIs return a detail field
2. Read the actual Pydantic/schema model for that endpoint
3. Compare field by field: wrong name, extra field, wrong type, forbidden empty string

**How to diagnose 404s on missing endpoints:**
1. Check the router file — does the endpoint exist?
2. If it doesn't exist and the UI needs it, add it to the API
3. Common missing endpoints: DELETE for sub-resources, GET for single items,
   archive/unarchive as dedicated POST endpoints

### Finding the Right Payload Shape

Always read the schema/model before writing a fix, not after. The source of truth is:

- **Pydantic models**: Look for `Create`, `Update`, `Patch` variants — they often differ
- **`extra='forbid'`**: Any field not in the model causes a 422 — remove extra fields
- **Required vs optional**: A required field with no default will 422 if omitted
- **Enums**: Free-text inputs for enum fields will 422 on any non-allowed value — replace
  with `<select>` dropdowns using the exact enum values from the schema
- **ID vs slug**: Many APIs store relationships as integer IDs. If the UI sends a slug where
  an ID is expected, the backend will reject it or silently ignore it

### Archive / Delete Patterns

Archive is not always a dedicated endpoint. Check what the entity's Update schema accepts:

- If the Update schema has `archived_at`, use `PATCH {archived_at: ISO_timestamp}`
- If the entity has a `status` field with an `abandoned` or `archived` value, use
  `PATCH {status: 'abandoned'}`
- Only use a dedicated `POST /archive` endpoint if it actually exists in the router

### Missing API Endpoints

If the UI calls an endpoint that doesn't exist, you have two options:
1. **Add the endpoint** — appropriate when the operation is clearly needed and fits the API's
   design (e.g. a missing DELETE for a sub-resource)
2. **Fix the UI** — appropriate when the UI invented a wrong endpoint and there's a correct
   alternative (e.g. calling `/archive` when the correct approach is a PATCH)

Always prefer fixing the UI to match a working endpoint over adding a new endpoint, unless
the operation genuinely doesn't have any current way to accomplish it.

---

## Step 5 — After Every Fix

After changing the API, rebuild and restart the API service before re-testing. Common pattern
for docker-compose projects:

```bash
docker compose -f <path>/docker-compose.yml build api
docker compose -f <path>/docker-compose.yml up -d api
```

Adapt to whatever the project uses — bare process, systemd, K8s, etc.

After changing the UI (HTML/JS), a hard reload in Playwright is sufficient if the files are
served statically:

```
playwright-browser_navigate: http://localhost:<port>
```

Then re-run the specific workflow that was failing. Confirm the fix works before moving on.

**Always check JS syntax before deploying UI changes:**
```bash
node --check /path/to/index.html  # or extract the script block to a temp file
```

A single syntax error in the script block can silently kill the entire JS runtime. There may
be no error message — the page will simply stop working.

---

## Step 6 — Verify the Full Workflow List Clean

After all individual workflow fixes are done, do a final pass:

1. Reload the page fresh: `playwright-browser_navigate http://localhost:<port>`
2. Check console errors on cold load — should be 0 real errors
3. Spot-check 3–4 of the most complex workflows end-to-end
4. Confirm the items created during testing appear correctly in their respective sections

If any new failures appear during the final pass, treat them as new iterations of Step 3
and fix them before declaring done.

---

## What Good Looks Like

A successful repair session produces:

- **0 console errors** on cold load and throughout all workflows
- Every workflow in the list can be executed without workarounds
- Creates produce items that appear in the UI immediately
- Saves persist (re-opening the record shows the updated values)
- Deletes/archives remove items from lists immediately
- All dropdowns for enum fields use `<select>` with the actual valid values
- All foreign key fields use datalists or searchable dropdowns populated from live data —
  no raw slug/ID text inputs requiring the user to know or copy/paste values
- Confirmation dialogs appear before destructive actions
- Error toasts appear when API calls fail

---

## Framework-Specific Pitfalls

### Alpine.js

- **Transient "X is not defined" on page load**: Alpine evaluates expressions before deferred
  scripts finish loading. These are harmless. Real errors are 404s, 422s, 500s, and uncaught
  exceptions.
- **Missing `async` on a function that uses `await`**: The function returns a Promise that is
  never awaited, the UI appears to do nothing, and there is no error. Always check that
  functions calling `api()` are declared `async`.
- **`extra='forbid'` on Pydantic models**: Any field sent to the API that isn't in the model
  causes a 422. Check the model before adding or keeping fields in the payload.
- **Empty string instead of null**: `estimated_effort: ''` causes a 422 if the field expects
  an enum or null. Use `|| null` for optional fields: `estimated_effort: this.form.effort || null`.
- **Wrong field name in API response**: The UI may read `note.content` but the API returns
  `note.body`. Always verify field names against the serializer output, not the model.
- **`PUT` instead of `PATCH`**: Most modern APIs use PATCH for partial updates. PUT causes a
  405 if the router only registers PATCH.
- **Silent error swallowing**: If `handleError` only logs to console without showing a toast,
  failures are invisible. Make sure error handling surfaces feedback to the user.

---

## Documentation After Repair

Before declaring done, create issue docs for any non-obvious bugs discovered:

```
docs/issues/YYYY_MM_DD_<slug>.md
```

Document:
- What the bug was (endpoint missing, wrong method, schema mismatch)
- What the correct fix was
- Any API endpoints added during repair

This record is useful when the same patterns appear in other UIs in the same stack.