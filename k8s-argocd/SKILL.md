---
name: k8s-argocd
description: 'Deploy, update, or add services to the home Kubernetes cluster. Use when the user asks to deploy something, add a service to k8s, update a helm chart, change cluster config, add DNS, or anything involving Kubernetes or ArgoCD.'
---

# Kubernetes / ArgoCD Deployment

All cluster changes deploy via git. **Never `kubectl apply` for anything managed by ArgoCD.**

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

| App | Repo | Branch | Namespace | Values |
|---|---|---|---|---|
| gyopart | `workspace/gyopart` | `main` | `gyopart` | `values.yaml` |
| gyopart-dev | `workspace/gyopart` | `dev` | `gyopart-dev` | `values-dev.yaml` |
| scrape-stack | scrape-stack repo | `main` | `scrape-stack` | — |
| scrape-stack-dev | scrape-stack repo | `dev` | `scrape-stack-dev` | — |

**To update:** edit Helm chart or values → commit → push to the appropriate branch.

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

---

## Docker Images (gyopart services)

Never use raw `docker build` or `docker push`. Always build and push from the gyopart repo root:
```bash
docker compose build <service> && docker compose push <service>
```
After pushing, restart the deployment to pull the new image:
```bash
kubectl rollout restart deployment/<name> -n gyopart-dev
```

Check `imagePullPolicy` in the relevant values file if pods keep running the old image after a push.

---

## DNS Changes

Edit `cluster_config/dns/dns.yaml` (CoreDNS ConfigMap zone file), bump the serial number, commit and push. CoreDNS does not hot-reload ConfigMaps automatically — after ArgoCD syncs, run:
```bash
kubectl rollout restart deployment/coredns-local -n dns
```

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
