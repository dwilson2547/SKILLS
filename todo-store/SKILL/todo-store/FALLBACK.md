# Curl Fallback — Todo Store API

Use these commands if the `todo` CLI is unavailable.

```bash
BASE_URL="${TODO_STORE_API_URL:-http://localhost:8003}"
```

## List todos

```bash
curl "${BASE_URL}/todos"
curl "${BASE_URL}/todos?status=open&priority=high"
curl "${BASE_URL}/todos?tags=bug,triage&q=inventory"
```

## Create a todo

```bash
curl -X POST "${BASE_URL}/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "Investigate flaky yard sync", "description": "Observed during importer retries", "tags": "bug,triage", "priority": "high", "status": "open"}'
```

## Get one todo

```bash
curl "${BASE_URL}/todos/42"
```

## Update a todo

```bash
curl -X PUT "${BASE_URL}/todos/42" \
  -H "Content-Type: application/json" \
  -d '{"priority": "urgent", "status": "in_progress"}'
```

## Complete a todo

```bash
curl -X PATCH "${BASE_URL}/todos/42/complete" \
  -H "Content-Type: application/json" \
  -d '{"completion_description": "Fixed while working on retry handling"}'
```

## Delete a todo

```bash
curl -X DELETE "${BASE_URL}/todos/42"
```

## Export todos

```bash
curl "${BASE_URL}/todos/export"
```

## Import todos

```bash
curl -X POST "${BASE_URL}/todos/import" \
  -H "Content-Type: application/json" \
  -d @todos.json
```
