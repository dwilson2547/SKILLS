# Curl Fallback — Notes Server API

Use these commands if the `notes` CLI is unavailable.

## Search (semantic)

```bash
curl "http://localhost:8000/notes/search?q=YOUR+QUERY&limit=5"
```

Returns: `[{"note": {...}, "score": 0.87}, ...]`

## Create a note

```bash
curl -X POST http://localhost:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Title", "tags": ["tag1", "tag2"], "content": "Key facts."}'
```

## Update a note

```bash
# Find the ID first
curl "http://localhost:8000/notes/search?q=topic&limit=3"

curl -X PUT http://localhost:8000/notes/{id} \
  -H "Content-Type: application/json" \
  -d '{"content": "Updated content."}'
```

## Get a note by ID

```bash
curl "http://localhost:8000/notes/{id}"
```

## Archive a note

```bash
curl -X POST http://localhost:8000/notes/{id}/archive
```
