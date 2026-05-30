---
name: work-manager
description: >
  Use this skill when pulling a task to work on, checking task criteria and definition of done,
  saving discoveries as notes, filing issue documents, or updating task progress. Work Manager
  (http://localhost:8010) is the central project planning system — epics, tasks, subtasks,
  acceptance criteria, testing layers, DoD, notes, and issue docs all live here.
applyTo: "**"
---

# Work Manager

Work Manager is the central project planning and agent execution system. All projects, epics,
tasks, notes, issues, and design docs live here. Agents pull work from it, execute tasks, save
their findings back to it, and cannot mark tasks complete unless all acceptance criteria and
testing layers are satisfied.

> If `workman` is not installed, follow [INSTALL.md](./INSTALL.md). If the CLI is unusable, see
> [FALLBACK.md](./FALLBACK.md) for curl commands.

---

## When to Use

- Pull the next task to work on
- Get the full context brief for a task (notes, design docs, sibling status, completion blockers)
- Update task status as work progresses
- Add or verify acceptance criteria
- Add or update testing layers
- Set or update the definition of done
- Save a new note with a scoped tag (discoveries, patterns, tooling notes)
- File an issue document when a problem is encountered or resolved
- Search for existing notes relevant to your work domain

---

## Core Agent Workflow

### 1 — Pull the next task

```bash
workman next
# or filter by project
workman next --project PROJECT-001
```

This returns a full markdown brief including:
- Task description and status
- Sibling task statuses
- Linked design doc excerpts
- Relevant notes (auto-matched by tag)
- Acceptance criteria
- Testing layers
- Definition of done
- Completion blockers (if any)

### 2 — Start the task

```bash
workman task update TASK-001 --status in_progress
```

### 3 — Check requirements before starting

```bash
workman task get TASK-001
```

Shows all acceptance criteria, testing layers, and DoD in one view.

### 4 — Work the task, then verify criteria

```bash
# Mark each acceptance criterion as verified
workman criterion check TASK-001 <id>

# Update testing layer statuses
workman testing update TASK-001 <id> --status passed
```

### 5 — Save discoveries as notes

```bash
workman note add "Title" "Body text" --tags scope:domain,technology
```

Notes require at least one `scope:` tag. Future briefs in the same domain will surface them.

### 6 — File issues if problems arise

```bash
workman issue add "Brief title" --task TASK-001 --severity sev2 \
  --root-cause "..." --resolution "..." --lessons "..."
```

### 7 — Mark complete (enforced)

```bash
workman task done TASK-001
```

The server will reject completion if acceptance criteria are unverified or testing layers have
unresolved failures. Fix blockers first — `workman brief TASK-001` shows what's blocking.

---

## Note Conventions

- Tags must use `scope:` prefix for at least one tag: `scope:api`, `scope:database`, `scope:auth`
- Additional context tags are fine: `scope:api,fastapi,pagination`
- Keep body under 2000 characters — concise findings only
- Notes are surfaced in task briefs when their scope tags overlap with the task's tags

---

## Quick Reference

```bash
# Briefs
workman brief TASK-001          # Full brief for a specific task
workman next                    # Brief for next ready task

# Project tree
workman projects                # All projects, epics, tasks

# Tasks
workman task ls                 # All tasks
workman task ls --status ready  # Filter by status
workman task get TASK-001       # Task + criteria + testing + DoD
workman task update TASK-001 --status in_progress
workman task done TASK-001
workman task create --epic EPIC-001 --title "..." --effort m

# Acceptance criteria
workman criterion ls TASK-001
workman criterion add TASK-001 "Must return 200 for valid input"
workman criterion check TASK-001 <id>

# Testing layers
workman testing ls TASK-001
workman testing add TASK-001 unit "Unit test all edge cases"
workman testing add TASK-001 integration "Verify API contract"
workman testing update TASK-001 <id> --status passed

# Definition of done
workman dod get TASK-001
workman dod set TASK-001 "All criteria verified, tests passing, PR merged"

# Notes
workman note ls
workman note ls --query "rate limiting" --mode semantic
workman note add "Title" "Body" --tags scope:api,ratelimit
workman note get NOTE-001

# Issues
workman issue ls
workman issue add "Auth token not refreshing" --task TASK-001 --severity sev2
workman issue resolve ISSUE-001 --resolution "Fixed token expiry logic"

# Export / import
workman export workman-backup.json
workman import workman-backup.json
```
