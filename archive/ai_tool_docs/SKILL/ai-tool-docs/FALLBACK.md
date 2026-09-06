# Fallback: curl commands for AI Tool Docs Server

Use these when the `docs` CLI is unavailable.

```bash
BASE="http://localhost:8002"

# Semantic search
curl -s "$BASE/docs/search?q=your+query+here&limit=10" | python3 -m json.tool

# Search within a specific source (replace 1 with source id)
curl -s "$BASE/docs/search?q=query&source_id=1&limit=10" | python3 -m json.tool

# List all sources
curl -s "$BASE/sources" | python3 -m json.tool

# Get source by id
curl -s "$BASE/sources/1" | python3 -m json.tool

# Add a source
curl -s -X POST "$BASE/sources" \
  -H "Content-Type: application/json" \
  -d '{"name":"mylib","repo":"owner/repo","branch":"main","docs_folders":["docs"],"file_glob":"*.md"}' \
  | python3 -m json.tool

# Trigger sync
curl -s -X POST "$BASE/sources/1/sync"

# List files for a source
curl -s "$BASE/sources/1/files" | python3 -m json.tool

# List sections for a file
curl -s "$BASE/docs?source_id=1&file_path=docs/getting-started.md" | python3 -m json.tool

# Get a single section
curl -s "$BASE/docs/42" | python3 -m json.tool

# Stats
curl -s "$BASE/stats" | python3 -m json.tool
```
