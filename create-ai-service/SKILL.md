---
name: create-ai-service
description: 'Create a new AI service — a skill-driven MCP-style service with a FastAPI backend, SQLite, SPA UI, Docker Compose, and a CLI layer. Use when the user asks to build an AI service, create a new agent-facing service, or add a new service to the SKILLS stack.'
---

# Create AI Service

AI services are lightweight, skill-driven services that agents interact with directly. Each has a
FastAPI backend, SQLite persistence, a single-page UI, a CLI layer, and a Docker Compose stack
that can be built, pushed, and run locally in one step.

---

## Step 1 — Assign a port

Scan all `docker-compose.yml` files in `/home/daniel/documents/workspace/SKILLS` to find the
highest API port in use, then increment by 1.

Current known ports: **8000–8003**. Next available: **8004** (verify by scanning first).

UI port convention: `3000 + (API port - 8000)`. Example: API on 8004 → UI on 3004.

---

## Step 2 — Directory structure

Create the following under `/home/daniel/documents/workspace/SKILLS/<service-name>/`:

```
<service-name>/
├── api/                  # FastAPI application
├── ui/                   # Single-page UI
├── data/                 # SQLite volume (gitignored)
├── scripts/
│   └── set-api-url.sh    # CLI config helper
├── docker-compose.yml
└── SKILL/
    └── <service-name>/
        ├── SKILL.md
        ├── INSTALL.md
        └── FALLBACK.md
```

---

## Step 3 — API

FastAPI app with:
- SQLite backend via SQLAlchemy
- `/health` endpoint
- `/docs` — auto-generated OpenAPI UI (FastAPI default)
- A human-readable `/` root endpoint (HTML page) documenting the API with usage examples — this is the docs endpoint agents read
- `GET /<resources>/export` — returns full dataset as JSON for migration
- `POST /<resources>/import` — accepts JSON, supports `merge` (default) and `replace` modes

Port is read from the environment:
```python
PORT = int(os.getenv("<SERVICE_NAME>_API_PORT", "<default_port>"))
```

Default URL env var: `<SERVICE_NAME>_API_URL`, defaulting to `http://localhost:<port>`.

---

## Step 4 — UI

Single-page application. Keep it simple — the UI is for human review, not the primary agent interface.

---

## Step 5 — Docker Compose

```yaml
services:
  api:
    build: ./api
    image: dwilson2547/<service-name>-api:0.1.0
    ports:
      - "<port>:<port>"
    volumes:
      - ./data:/data
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:<port>/health', timeout=5)"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - <service-name>-net

  ui:
    build: ./ui
    image: dwilson2547/<service-name>-ui:0.1.0
    ports:
      - "<ui-port>:80"
    depends_on:
      api:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - <service-name>-net

networks:
  <service-name>-net:
```

---

## Step 6 — CLI layer

Create `scripts/set-api-url.sh` following the pattern from `todo-store/scripts/set-api-url.sh`:
accepts a host or full URL, writes `export <SERVICE_NAME>_API_URL=...` into `~/.bashrc`,
prints instructions to `source` the file.

Create a Python CLI script at `SKILL/<service-name>/<cli-name>.py` that wraps the API.
The CLI must read the API URL from `<SERVICE_NAME>_API_URL` env var, falling back to
`http://localhost:<port>`. Include `export` and `import` subcommands that call the export/import
endpoints — these are the primary migration path.

---

## Step 7 — SKILL files

**`SKILL/<service-name>/SKILL.md`** — the agent-facing skill. Include:
- Trigger description (what makes an agent invoke this)
- How to use the CLI (primary interface)
- Pointer to INSTALL.md if CLI not present
- Pointer to FALLBACK.md for curl commands

**`SKILL/<service-name>/INSTALL.md`** — how to install the CLI:
```markdown
## Install

Copy `<cli-name>.py` to a directory on your PATH and make it executable, or symlink it:

```bash
ln -s $(pwd)/SKILL/<service-name>/<cli-name>.py ~/.local/bin/<cli-name>
chmod +x ~/.local/bin/<cli-name>
```
```

**`SKILL/<service-name>/FALLBACK.md`** — curl equivalents for every CLI command.

---

## Step 8 — Register the skill

Add an explicit mapping to `install_skill_symlinks.sh` in the SKILLS repo root:

```bash
skill_targets["<service-name>"]="${SCRIPT_DIR}/<service-name>/SKILL/<service-name>"
```

Then run:
```bash
./install_skill_symlinks.sh
```

---

## Step 9 — Commit

Commit everything to the SKILLS repo:
```bash
cd /home/daniel/documents/workspace/SKILLS
git add <service-name>/ install_skill_symlinks.sh
git commit -m "feat: add <service-name> ai service"
```

---

## Rules

- Never reuse a port — always scan compose files first
- Image names follow `dwilson2547/<service-name>-api:<version>` and `dwilson2547/<service-name>-ui:<version>`
- The service must work with plain `docker compose up` — no external dependencies beyond what's in the compose file
- The CLI must be the primary agent interface; curl fallbacks are for emergencies only
- Always commit to the SKILLS repo, never to the project repo
