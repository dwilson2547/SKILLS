# Curl Fallback — Work Manager API

Use these commands if the `workman` CLI is unavailable.

```bash
BASE="${WORKMAN_API_URL:-http://localhost:8010}"
```

## Get next task brief (markdown)

```bash
SLUG=$(curl -s "${BASE}/tasks/next" | python3 -c "import sys,json; print(json.load(sys.stdin).get('slug',''))")
curl -s "${BASE}/briefs/task/${SLUG}/markdown"
```

## Get brief for a specific task

```bash
curl -s "${BASE}/briefs/task/TASK-001/markdown"
```

## List tasks

```bash
curl -s "${BASE}/tasks"
curl -s "${BASE}/tasks?status=ready"
curl -s "${BASE}/tasks?project=PROJECT-001"
```

## Get task detail

```bash
curl -s "${BASE}/tasks/TASK-001"
curl -s "${BASE}/tasks/TASK-001/acceptance-criteria"
curl -s "${BASE}/tasks/TASK-001/testing-layers"
curl -s "${BASE}/tasks/TASK-001/dod"
```

## Update task status

```bash
curl -s -X PATCH "${BASE}/tasks/TASK-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

## Mark task complete

```bash
curl -s -X PATCH "${BASE}/tasks/TASK-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "complete"}'
```

## Create a task

```bash
curl -s -X POST "${BASE}/epics/EPIC-001/tasks" \
  -H "Content-Type: application/json" \
  -d '{"title": "Implement feature X", "description": "...", "estimated_effort": "m"}'
```

## Add acceptance criterion

```bash
curl -s -X POST "${BASE}/tasks/TASK-001/acceptance-criteria" \
  -H "Content-Type: application/json" \
  -d '{"description": "Must return 200 for valid input"}'
```

## Verify acceptance criterion

```bash
curl -s -X PATCH "${BASE}/tasks/TASK-001/acceptance-criteria/1" \
  -H "Content-Type: application/json" \
  -d '{"verified": true}'
```

## Add testing layer

```bash
curl -s -X POST "${BASE}/tasks/TASK-001/testing-layers" \
  -H "Content-Type: application/json" \
  -d '{"layer": "unit", "description": "Unit test all edge cases"}'
```

## Update testing layer status

```bash
curl -s -X PATCH "${BASE}/tasks/TASK-001/testing-layers/1" \
  -H "Content-Type: application/json" \
  -d '{"status": "passed"}'
```

## Set definition of done

```bash
curl -s -X PATCH "${BASE}/tasks/TASK-001/dod" \
  -H "Content-Type: application/json" \
  -d '{"dod_description": "All criteria verified, tests passing, PR merged"}'
```

## Add a note

```bash
curl -s -X POST "${BASE}/notes" \
  -H "Content-Type: application/json" \
  -d '{"title": "Rate limit pattern", "body": "Use token bucket via request-auth...", "tags": ["scope:api", "ratelimit"]}'
```

## Search notes

```bash
curl -s "${BASE}/notes?q=rate+limiting&mode=semantic"
curl -s "${BASE}/notes?tag=scope:api"
```

## File an issue

```bash
curl -s -X POST "${BASE}/issues" \
  -H "Content-Type: application/json" \
  -d '{"title": "Auth token not refreshing", "severity": "sev2", "task_slug": "TASK-001", "root_cause": "...", "resolution": "..."}'
```

## Resolve an issue

```bash
curl -s -X PATCH "${BASE}/issues/ISSUE-001" \
  -H "Content-Type: application/json" \
  -d '{"status": "resolved", "resolution": "Fixed token expiry logic"}'
```

## List projects

```bash
curl -s "${BASE}/projects"
```

## Export all data

```bash
curl -s "${BASE}/projects/export" > projects.json
curl -s "${BASE}/tasks/export" > tasks.json
curl -s "${BASE}/notes/export" > notes.json
```
