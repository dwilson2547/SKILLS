# Curl Fallback — Playbooks Server API

Use these commands if the `playbooks` CLI is unavailable.

## List all slugs

```bash
curl "http://localhost:8001/slugs"
curl "http://localhost:8001/slugs?scope=junkyard-scraper"
```

## List documents

```bash
curl "http://localhost:8001/playbooks?status=active"
curl "http://localhost:8001/playbooks?scope=junkyard-scraper"
```

## Ingest a document

```bash
curl -X POST http://localhost:8001/playbooks \
  -H "Content-Type: application/json" \
  -d "{\"slug\": \"junkyard-scraper/auth\", \"title\": \"Auth Strategy\",
       \"content\": \"$(cat auth.md | sed 's/\"/\\\"/g')\",
       \"tags\": \"scraper,auth\"}"
```

## Semantic search

```bash
curl -X POST http://localhost:8001/playbooks/search \
  -H "Content-Type: application/json" \
  -d '{"query": "OAuth token refresh", "scope": "junkyard-scraper", "limit": 5}'
```

## Get table of contents

```bash
curl "http://localhost:8001/playbooks/junkyard-scraper/auth/toc"
```

## Get a section

```bash
curl "http://localhost:8001/playbooks/junkyard-scraper/auth/sections/oauth-flow"
```

## Get full document

```bash
curl "http://localhost:8001/playbooks/junkyard-scraper/auth"
```

## Update document

```bash
curl -X PUT http://localhost:8001/playbooks/junkyard-scraper/auth \
  -H "Content-Type: application/json" \
  -d '{"content": "# Updated content\n\n..."}'
```

## Mark stale

```bash
curl -X PATCH http://localhost:8001/playbooks/junkyard-scraper/auth/status \
  -H "Content-Type: application/json" \
  -d '{"status": "stale"}'
```

## Delete

```bash
curl -X DELETE http://localhost:8001/playbooks/junkyard-scraper/auth
```
