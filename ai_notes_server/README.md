# AI Notes Server

Lightweight knowledge persistence for AI agents. Notes survive across sessions, enabling agents to build on prior findings instead of re-discovering the same patterns.

<img width="869" height="923" alt="image" src="https://github.com/user-attachments/assets/d2ce3e04-9033-4361-8fcf-288718de6213" />


## Stack

- **API** — FastAPI + SQLite + [fastembed](https://github.com/qdrant/fastembed) (`BAAI/bge-small-en-v1.5` via ONNX — no PyTorch)
- **UI** — Alpine.js SPA served by nginx
- **Data** — `./data/notes.db` (SQLite, persisted via volume mount)

## Ports

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| API Guide | http://localhost:8000/instructions |
| UI | http://localhost:3000 |

## Commands

**Start**
```bash
docker compose up -d
```

**Stop**
```bash
docker compose down
```

**Restart**
```bash
docker compose restart
```

**Rebuild after code changes**
```bash
docker compose up -d --build
```

**View logs**
```bash
docker compose logs -f
docker compose logs -f api
```

## Notes

- The first `docker compose up --build` will take a few minutes — the embedding model (~130 MB) is downloaded during the API image build.
- The SQLite database is stored in `./data/notes.db` and survives rebuilds.
- The UI proxies `/api/*` requests to the API container — no CORS configuration needed in the browser.
- Agents can connect directly to the API at `http://localhost:8000`. Start at `/instructions` to understand the API.

## Agent Skill

A skill file for agents is at [.agents/skills/ai-notes-server/SKILL.md](../../../.agents/skills/ai-notes-server/SKILL.md).
