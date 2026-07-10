---
name: work-manager
description: >
  DEPRECATED — Work Manager (workman, localhost:8010) is retired along with the rest of
  the service knowledge stack. Notes live in <domain>/docs/notes/ via meta/bin/wsnote;
  backlogs are TODO.md at project roots; plans/guides are files in <project>/docs/ or
  <domain>/docs/topics/; issues go to <project>/docs/issues/ via the issue-documentation
  skill. Do not use the workman CLI or any localhost:8010 endpoint.
---

# Work Manager — RETIRED (repo-native now)

> ⚠️ Retired 2026-07. All content (notes, playbooks, todos, draft tasks, issues,
> context docs) was exported to the workspace repo. The historical db remains readable
> at `meta/SKILLS/work-manager/data/workman.db` (SQLite) but nothing should write to it.

Where things live now (CONVENTIONS.md §5):
- **Notes** → `docs/notes/` folders, `meta/bin/wsnote` CLI
- **Backlogs** → `TODO.md` at project root
- **Issues** → `<project>/docs/issues/` (issue-documentation skill)
- **Guides/plans** → `<domain>/docs/topics/` or `<project>/docs/`
