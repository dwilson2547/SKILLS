# Archive project endpoint returns 500 because `archived_at` schema type rejects ISO strings

**Date:** 2026-05-30  
**Component:** `api/app/schemas.py` — `ProjectUpdate`  
**Severity:** High — archiving projects was completely broken; clicking the Archive button always produced a 500

---

## Observed symptom

Clicking the "Archive" button on a project, confirming the dialog, produced a 500 Internal Server
Error. The docker logs showed:

```
sqlalchemy.exc.StatementError: (builtins.TypeError) SQLite DateTime type only accepts Python
datetime and date objects as input.
```

The UI's `archiveProject()` function sends `PATCH /api/projects/{slug}` with
`{ archived_at: new Date().toISOString() }` — a valid ISO 8601 string such as
`"2026-05-31T02:56:06.259Z"`.

---

## Root cause

### `archived_at` annotated as `str | None` instead of `datetime | None`

`ProjectUpdate` in `schemas.py` declared the field as:

```python
archived_at: str | None = None
```

Pydantic v2 with `str | None` accepts and passes through the raw ISO string without parsing it.
When SQLAlchemy's `DateTime` column type receives a plain string, it raises a `TypeError` because
it only accepts Python `datetime` or `date` objects.

The correct annotation is `datetime | None`, which causes Pydantic to parse the ISO string into a
`datetime` object before it is handed to SQLAlchemy.

---

## Troubleshooting steps taken

1. **Checked docker logs** — `SQLite DateTime type only accepts Python datetime and date objects`
   pointed directly at the SQLAlchemy layer, ruling out a networking or routing issue.

2. **Traced the PATCH handler** — `routers/projects.py` uses `payload.model_dump(exclude_unset=True)`
   and a `setattr` loop; no special handling for `archived_at`, so the raw Pydantic-parsed value
   reaches SQLAlchemy unchanged.

3. **Inspected the schema** — confirmed `archived_at: str | None` was the culprit; Pydantic
   passes strings through unchanged, while `datetime | None` triggers automatic ISO parsing.

---

## Fix

### `api/app/schemas.py` — Change `archived_at` type and add import

Added `from datetime import datetime` at the top of the file. Changed the field type in
`ProjectUpdate`:

```python
# Before
archived_at: str | None = None

# After
archived_at: datetime | None = None
```

Pydantic v2 automatically coerces an ISO 8601 string to a `datetime` object when the field is
annotated as `datetime | None`, so no change to the router or UI was needed.

---

## Files changed

- `api/app/schemas.py` — `ProjectUpdate.archived_at` type annotation; added `datetime` import
