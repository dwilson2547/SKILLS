# Todo Store

Lightweight todo capture and tracking for AI agents. Todo Store gives agents a central place to save follow-ups, bug findings, and loose work items before they get lost during triage.

## Stack

- **API** — FastAPI + SQLite
- **UI** — Alpine.js SPA served by nginx
- **Data** — `./data/todos.db` (persisted with a local path mount)

## Ports

| Service | URL |
|---------|-----|
| API | http://localhost:8003 |
| API Docs | http://localhost:8003/docs |
| API Guide | http://localhost:8003/instructions |
| UI | http://localhost:3003 |

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
docker compose logs -f ui
```

## Kubernetes

The cluster deployment for Todo Store follows the shared `ai-services` pattern in the `cluster_config` repo rather than keeping a separate chart here. The Kubernetes resources live under:

- `cluster_config/ai-services/deployment.yml`
- `cluster_config/dns/dns.yaml`
- `cluster_config/homepage/homepage.yaml`

## DNS and local env

Point the chosen Todo Store host at your cluster ingress endpoint, then update the local CLI base URL so `todo` targets the cluster API path:

```bash
./scripts/set-api-url.sh todo.ai-services.local
source ~/.bashrc
```

That writes `TODO_STORE_API_URL=http://todo.ai-services.local/api` into `~/.bashrc`. If you prefer, you can pass a full URL instead:

```bash
./scripts/set-api-url.sh http://todo.ai-services.local/api
```

## Notes

- Todos persist in `./data/todos.db` across rebuilds.
- JSON is the canonical import/export format.
- In Docker Compose, the UI proxies `/api/*` requests to the API container so browser traffic stays same-origin.
- In Kubernetes, Ingress owns `/api/*` routing and the UI nginx config is overridden to remove the compose-only proxy block.
- Agents should usually interact through the `todo` CLI rather than calling the API directly.

## Agent Skill

The associated agent skill lives at `todo-store/SKILL/todo-store/SKILL.md`.
