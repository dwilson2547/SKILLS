---
name: k8s-argocd
description: 'Deploy, update, or add services to the home Kubernetes cluster. Use when the user asks to deploy something, add a service to k8s, update a helm chart, change cluster config, add DNS, or anything involving Kubernetes or ArgoCD.'
---

# Kubernetes / ArgoCD Deployment

All cluster changes deploy via git. **Never `kubectl apply` for anything managed by ArgoCD.**

---

## Which Pattern to Use

**Helm chart in its own repo** — multi-service systems that are deployed as a unit:
- gyopart (api, ui, inventory-api, admin-api)
- scrape-stack (webcache, imgcache, request-auth, browserless, etc.)
- DanWiki, Photo-Dump, and similar future systems

These have their own git repo, their own Helm chart, and a `main`/`dev` branch strategy for prod vs dev. ArgoCD app manifests live either in the system's repo or in cluster_config — check the existing pattern for each system.

**cluster_config manifests** — everything else:
- Core infrastructure: postgres, monitoring, DNS, ingress
- Small standalone services where a dedicated helm repo would be overkill: homepage, ddclient, vpn, searxng

If it's one or two services with no dev/prod split needed, cluster_config is the right home.

---

## Two Deployment Patterns

### 1. Manifest-based — `cluster_config` repo
Plain Kubernetes manifests at `workspace/cluster_config/`. ArgoCD auto-syncs on push to `main`.

| Service | Directory | ArgoCD App |
|---|---|---|
| ai-services | `ai-services/` | `argocd/ai-services.yaml` |
| monitoring | `monitoring/` | `argocd/monitoring.yaml` |
| postgres | `postgres/` | `argocd/postgres.yaml` |
| homepage | `homepage/` | `argocd/homepage.yaml` |
| dns | `dns/` | `argocd/dns.yaml` |

**To update:** edit manifests → commit → push to `main`. ArgoCD handles the rest.

### 2. Helm-based — external repos (gyopart, scrape-stack)
These repos manage their own Helm charts and use a branch strategy for environments:

| App | Repo | Branch | Namespace | Domain | Values |
|---|---|---|---|---|---|
| gyopart | `workspace/gyopart` | `main` | `gyopart` | `gyopart.local` | `values.yaml` |
| gyopart-dev | `workspace/gyopart` | `dev` | `gyopart-dev` | `gyopart-dev.local` | `values-dev.yaml` |
| scrape-stack | `workspace/web_scrapers/scrape_stack` | `main` | `scrape-stack` | `scrapestack.local` | `values.yaml` |
| scrape-stack-dev | `workspace/web_scrapers/scrape_stack` | `dev` | `scrapestack-dev` | `scrapestack-dev.local` | `values-dev.yaml` |
| robo-services | `workspace/robo-services` | `main` | `robo-services` | `*.robo-services.local` | `helm/robo-services/values.yaml` |

**To update:** edit Helm chart or values → commit → push to the appropriate branch.

**Scrape-stack** services: browserless, request-auth-server/api/ui, webcache, imgcache, filecache, vidcache, cache-browser-api/ui.
Helm: `helm/scrape-stack/`. ArgoCD manifests live in the scrape-stack repo at `argocd/scrape-stack.yaml` + `argocd/scrape-stack-dev.yaml` — apply manually when changed.
Image updates: dev uses `imagePullPolicy: Always` (push → auto-rollout on next sync); prod requires an explicit tag bump in `values.yaml`.

**Gyopart** services: gyopart-api (:8200), gyopart-ui (:80), inventory-api (:8100), admin-api (:8300).
Helm: `gyopart/helm/gyopart/`. ArgoCD manifests: `cluster_config/argocd/gyopart.yaml` + `gyopart-dev.yaml`.
Always build/push from the gyopart root: `docker compose build <service> && docker compose push <service>`.
After pushing: `kubectl rollout restart deployment/<name> -n gyopart-dev`.

---

## Exceptions — manual `kubectl apply` required

### Secrets (never committed)
```bash
kubectl apply -f <service>/secret.yml
```
Templates in `cluster_config/example-secrets/` and per-service `secret.yml` files. Fill in real values, never commit them.

### ArgoCD Application manifests
Every time an `argocd/*.yaml` file changes, it must **also** be applied manually — ArgoCD does not manage its own Application CRs:
```bash
kubectl apply -f /home/daniel/documents/workspace/cluster_config/argocd/<service>.yaml
```
For gyopart specifically:
```bash
kubectl apply -f /home/daniel/documents/workspace/cluster_config/argocd/gyopart-dev.yaml
kubectl apply -f /home/daniel/documents/workspace/cluster_config/argocd/gyopart.yaml
```
Git push alone is not enough for these files.

---

## Adding a New Service (manifest-based)

1. Create `cluster_config/<service-name>/` with manifests
2. Add `cluster_config/argocd/<service-name>.yaml` pointing at `path: <service-name>`
3. Apply the ArgoCD app manually: `kubectl apply -f argocd/<service-name>.yaml`
4. Create namespace and apply secrets if needed
5. Push to `main` for all subsequent changes

## Deploying a New Service (complete these steps as applicable)

When deploying a new service, complete each of the following steps **only if applicable**, but do not skip them when they apply — do not stop after the pod is running:

1. **Enable ingress** — only if the service exposes an HTTP endpoint that should be reachable on the local network. Set `ingress.enabled: true` and pick a hostname like `<service>.<system>.local`.
2. **Add DNS** — only if ingress was enabled (or a LoadBalancer IP was assigned). Add an A record to the appropriate zone file in `cluster_config/dns/dns.yaml`, bump the serial, commit and push.
3. **Add homepage entry** — only if the service has a UI or a browsable endpoint (Swagger docs, dashboards, etc). Add to the relevant group in `cluster_config/homepage/homepage.yaml`, or create a new group if there isn't one yet.
4. **Update the changelog** — **always required** when any change is made to `cluster_config`. Update `cluster_config/CHANGELOG.md` with a dated entry describing what was added, changed, or fixed. The changelog is non-negotiable — no cluster_config commit should go out without it.

After pushing both repos, refresh the relevant ArgoCD apps and verify each change took effect.

---

## DNS Changes

Edit `cluster_config/dns/dns.yaml` (CoreDNS ConfigMap zone file), bump the serial number, commit and push. The `coredns-local` Deployment is annotated with `configmap.reloader.stakater.com/reload: coredns-local-config`, so Stakater Reloader should roll CoreDNS automatically when ArgoCD applies the updated ConfigMap. Only fall back to a manual `kubectl rollout restart deployment/coredns-local -n dns` if reloader is unavailable or the rollout does not happen.

---

## Key Ingress Hostnames

| Host | Service |
|---|---|
| `gyopart.local` | gyopart UI |
| `api.gyopart.local` | gyopart API |
| `admin.gyopart.local` | admin API |
| `inventory.gyopart.local` | inventory API |
| `gyopart-dev.local` | gyopart-dev UI (dev equivalents follow this pattern) |
| `argocd.local` | ArgoCD UI |
| `notes.ai-services.local` | AI Notes |
| `home.cluster.local` | Homepage dashboard |

---

## Rules

- Never `kubectl apply` for ArgoCD-managed resources — git push is the deployment mechanism
- Never commit secrets — apply them manually
- ArgoCD Application manifests (`argocd/*.yaml`) require both a git push AND a manual `kubectl apply`
- The `kubernetes/` directory in cluster_config is legacy/archive — not actively synced by ArgoCD
- Do not run `kubectl apply` against the gyopart Helm chart — ArgoCD owns it

---

## Documentation Closure

Before declaring the task complete, scan the work you just did for anything worth capturing.

**Issue docs** — create `docs/issues/YYYY_MM_DD_<slug>.md` in the project repo for:
- Any pod/service that entered CrashLoopBackOff or failed to start
- Any dependency, permission, or configuration that wasn't obvious from the code
- Any step you had to retry or that failed with an error before succeeding
- Any behavior that contradicted what the docs or code implied

**Patterns docs** — add a section to `docs/<technology>_patterns.md` (create if absent) for:
- Any non-obvious solution that would save time next time
- Any version constraint, API contract, or framework gotcha that bit you

**Notes** — for any new or updated doc, add or update a note pointing to it:
```bash
notes add "title" "2-5 sentence summary. See: docs/<file>.md" --tags technology,project
```

**Skip this step only if** the work was a purely mechanical change — single-value config edits,
no debugging, no retries, no surprises. If anything went wrong, even briefly, document it.
