---
name: docker-compose-creation
description: 'Create, fix, or improve docker-compose files. Use when writing a new docker-compose.yml, debugging compose startup failures, or adding services to an existing stack. Checks for port conflicts, confirms port changes with the user, prefers local storage paths over named volumes (asks when data is disposable), and verifies the stack starts successfully before declaring done. Also generates a concise README with start/stop/restart/rebuild commands.'
---

# Docker Compose Creation

A docker-compose stack is not complete until it has been brought up and all services confirmed healthy. Also generate a short README before finishing.

## Procedure

### 1. Check ports before writing the file

Before assigning any host ports, check what is already in use:

```bash
ss -tlnp | awk 'NR>1 {print $4}' | grep -oP '(?<=:)\d+$' | sort -n
# or
docker ps --format 'table {{.Ports}}' | grep -oP '\d+(?=->)' | sort -n
```

- If a desired port is taken, pick a free alternative.
- **Always confirm with the user before changing a port from what was originally requested.**

### 2. Decide on storage

For each service with persistent data, ask:

> "Does `<service>` hold data you want to keep across rebuilds (e.g. a database, uploaded files)? Or is it disposable (cache, temp processing)?"

- **Persistent / important data** → use a local path mount:
  ```yaml
  volumes:
    - ./data/servicename:/var/lib/service
  ```
- **Disposable data** → ask the user if a named Docker volume is acceptable:
  ```yaml
  volumes:
    - servicename_data:/var/lib/service
  volumes:
    servicename_data:
  ```
  Do not silently choose a named volume for anything that looks like it holds user data.

### 3. Write docker-compose.yml

Apply the guidelines below, then create the file.

### 4. Bring the stack up and verify

```bash
docker compose up -d
```

Check all services are running — none should be in `Exit` or `Restarting` state:

```bash
docker compose ps
```

If any service is unhealthy, check logs and fix:

```bash
docker compose logs <service>
```

Iterate until `docker compose ps` shows all services as `Up` (or `healthy` if healthchecks are defined).

### 5. Write the README

Create a `README.md` alongside the compose file. Keep it short — just the commands a user needs day-to-day:

```markdown
## <Stack Name>

**Start**
```
docker compose up -d
```

**Stop**
```
docker compose down
```

**Restart a service**
```
docker compose restart <service>
```

**Rebuild and restart**
```
docker compose up -d --build
```

**Logs**
```
docker compose logs -f <service>
```
```

---

## Authoring Guidelines

### Service definitions

- Always pin image versions (`image: postgres:16`) — never use `latest` in production configs.
- Set `restart: unless-stopped` for services that should survive host reboots.
- Use `depends_on` with `condition: service_healthy` when start order matters (requires a `healthcheck` on the dependency).

### Healthchecks

Add healthchecks to any service others depend on:

```yaml
healthcheck:
  test: ["CMD", "pg_isready", "-U", "postgres"]
  interval: 5s
  timeout: 3s
  retries: 5
```

### Environment variables

- Prefer a `.env` file for secrets and environment-specific values — never hardcode passwords in `docker-compose.yml`.
- Reference them as `${VAR_NAME}` in the compose file.
- Create a `.env.example` with placeholder values if secrets are needed.

### Networks

- Define an explicit named network rather than relying on the default compose network — it makes inter-service DNS predictable:
  ```yaml
  networks:
    app-net:
  ```
  Then attach each service: `networks: [app-net]`

### Local path mounts

- Use relative paths from the compose file location (`./data/postgres`) so the stack is portable.
- Create the directories before first `up` or note this in the README if manual setup is needed.
- Ensure the host path is owned by the correct UID if the container runs as a non-root user.

### Port mapping

- Format: `"host:container"` with quotes to avoid YAML octal parsing issues.
- Only expose ports to the host that actually need to be reachable externally — internal service-to-service traffic uses the compose network, not host ports.
