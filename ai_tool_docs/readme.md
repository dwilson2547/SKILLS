# AI Tool Docs Server

A local documentation index for AI agents — think of it as a self-hosted Context7 for
libraries that Context7 doesn't cover. Pull markdown docs from any public GitHub repository,
index them with semantic embeddings, and query them from the CLI or through the management UI.

## Quick Start

```bash
# Start the stack
docker compose up -d

# Install the CLI
bash SKILL/ai-tool-docs/INSTALL.md   # or follow instructions manually

# Add a source and sync it
docs add "ghz" --repo bojand/ghz --folders docs
docs search "how to set rps and concurrency"
```

## Services

| Service | URL |
|---------|-----|
| API     | http://localhost:8002 — REST API + Swagger at `/docs` |
| UI      | http://localhost:3002 — Management UI |

## docker-compose Commands

```bash
docker compose up -d          # start
docker compose down           # stop
docker compose down -v        # stop + remove data volume
docker compose build          # rebuild images after code changes
docker compose logs -f api    # follow API logs
```

## How It Works

1. **Add a source** — provide a GitHub `owner/repo`, branch, optional subdirectory paths, and file glob (default `*.md`).
2. **Sync** — the API fetches the latest commit SHA. If it differs from the stored SHA, it downloads changed files, parses them into sections by heading, and stores embeddings.
3. **Daily updates** — a background scheduler checks all sources every 24 hours and re-indexes only changed files.
4. **Search** — semantic search across all indexed sections using cosine similarity (BAAI/bge-small-en-v1.5).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | _(none)_ | Optional GitHub PAT. Raises rate limit from 60→5000 req/hr and enables private repos. |

Set it in a `.env` file at the project root:
```
GITHUB_TOKEN=ghp_your_token_here
```

## CLI Reference

```bash
docs search "query"           # semantic search (all sources)
docs search "query" --source 1 --limit 10
docs get <id>                 # view full section content
docs sources                  # list all sources
docs source <id>              # show one source
docs add <name> --repo owner/repo [--branch main] [--folders docs,guides] [--glob "*.md"]
docs sync <id>                # force re-index
docs delete <id>              # remove source + sections
docs stats                    # aggregate counts
```

## Project Structure

```
ai_tool_docs/
├── api/                  FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py       App entry point + instructions page
│       ├── database.py   SQLite via SQLAlchemy
│       ├── models.py     Source, DocSection
│       ├── schemas.py    Pydantic I/O models
│       ├── embeddings.py fastembed BAAI/bge-small-en-v1.5
│       ├── sections.py   Markdown heading parser
│       ├── github_client.py  GitHub API (stdlib urllib, no extra deps)
│       ├── sync.py       Sync logic with per-source locking
│       ├── scheduler.py  APScheduler 24h background job
│       └── routers/
│           ├── sources.py   CRUD + sync trigger + file listing
│           └── docs.py      Search + list + stats
├── ui/                   Single-file Alpine.js management UI
│   ├── Dockerfile
│   ├── nginx.conf        Reverse-proxies /api/ → api:8002
│   └── index.html
├── SKILL/
│   └── ai-tool-docs/
│       ├── SKILL.md      Agent skill definition
│       ├── INSTALL.md    CLI installation instructions
│       ├── FALLBACK.md   curl commands when CLI unavailable
│       └── docs.py       Self-contained Python CLI
├── data/                 (gitignored) SQLite database
├── docker-compose.yml
└── .gitignore
``` 