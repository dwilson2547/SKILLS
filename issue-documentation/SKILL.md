---
name: issue-documentation
description: 'Document bugs and incidents as structured issue files during troubleshooting. Use when debugging a problem, investigating unexpected behavior, diagnosing a production incident, or after a root cause is identified. Creates docs/issues/ under the project root (creating docs/ too if absent), writes a dated issue file following the standard format, optionally adds a changelog entry referencing the issue file if a CHANGELOG exists, and persists the result into context-store and notes when those tools are available.'
argument-hint: 'Short description of the problem being documented'
---

# Issue Documentation

## When to Use

Invoke this skill whenever you are actively troubleshooting a problem in a project and want to
record findings as a structured issue document. Typical triggers:

- Root cause of a bug has been identified
- Unexpected behavior is observed and investigation begins
- A production incident is being documented post-mortem
- A fix is being applied that warrants a written record

---

## Procedure

### 1. Locate the project root

Identify the root directory of the project being worked on. This is usually the workspace folder
or the folder containing the primary source code, `go.mod`, `package.json`, `pyproject.toml`, etc.

### 2. Ensure the docs/issues/ path exists

Check whether `<project-root>/docs/` and `<project-root>/docs/issues/` exist. Create whichever
directories are missing. Do **not** create any placeholder files inside them.

### 3. Determine the filename

Use the format: `YYYY_MM_DD_<slug>.md`

- `YYYY_MM_DD` — today's date
- `<slug>` — a short, lowercase, underscore-separated label derived from the problem title
  (e.g. `pool_shrink_phantom_permits`, `auth_token_expiry_race`, `oom_on_large_payload`)

### 4. Write the issue document

Follow the [issue template](./assets/issue_template.md) exactly. Fill every section with the
information gathered during troubleshooting. Leave a section header with a `_TBD_` placeholder
only if the information is genuinely unknown at the time of writing — do not omit sections.

Key conventions:
- **Title** should be a single sentence that fully describes the bug/symptom as a cause–effect
  statement (e.g. "Pool shrink creates phantom permits, doubling throughput after live config change").
- **Component** should identify the file(s) and function(s) most directly responsible.
- **Severity** should be one of: `Critical`, `High`, `Medium`, `Low`, with a brief rationale.
- **Root cause** subsections use `###` and describe the mechanics, not just the symptoms. Include
  code snippets where they clarify the problem.
- **Troubleshooting steps** are numbered and written in past tense. Each step states what was
  checked and what was ruled in or out.
- **Fix** subsections use `###` named after the location/function changed. Include before/after
  code snippets where helpful.
- **Files changed** is a bullet list of `file — function/section` entries.

### 5. Check for a changelog

Search the project root for a changelog file. Common names: `CHANGELOG.md`, `CHANGELOG`,
`CHANGES.md`, `HISTORY.md`. If one exists:

- Prepend a new entry at the top of the changelog (or insert under an `## Unreleased` section if
  present) in the following format:

```
### Fixed
- <one-line summary of the fix> — see [docs/issues/<filename>](docs/issues/<filename>)
```

- Use the existing heading style already present in the changelog (e.g. if it uses `##` for
  versions, match that level for the entry).

If no changelog exists, skip this step silently.

### 6. Persist to context-store and notes

If `context`/context-store and `notes` are available, persist the issue after writing it:

- Ingest the issue document into context-store with a stable slug such as
  `<project-slug>/<issue-slug>` or `issues/<issue-slug>`
- Then add or update a short note summarising the problem/fix and pointing to the
  context-store slug
- Prefer updating an existing note over creating a duplicate

Suggested pattern:

```bash
context ingest docs/issues/YYYY_MM_DD_issue_slug.md \
  --slug "project/issues/issue-slug" \
  --description "Root cause and fix for <short problem summary>" \
  --tags "bug,incident,<project>"

notes search "<problem summary>"
notes add "Issue: <short problem summary>" \
  "Issue documented. Root cause and fix captured. Full write-up: context-store: project/issues/issue-slug" \
  --tags bug,incident,<project>
```

If either tool is unavailable, skip that persistence step silently and continue.

### 7. Confirm output

Report the path of the newly created issue file and, if applicable, the changelog file updated.
Mention the context-store slug and/or note only if they were created or updated. Do not summarise
the contents back to the user unless asked.
