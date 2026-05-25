---
name: scrape-stack
description: 'Deploy, update, or modify the scrape-stack system. Use when the user asks to update scrape-stack, change webcache/imgcache/filecache/vidcache/request-auth/browserless/cache-browser, add a new scrape-stack service, or change scrape-stack config.'
---

# Scrape-Stack Deployment

Scrape-stack is a self-contained multi-service scraping infrastructure system with its own Helm
chart and branch-based prod/dev environments. All changes deploy via git push.

**Repo:** `workspace/web_scrapers/scrape_stack/`
**Helm chart:** `helm/scrape-stack/`
**ArgoCD app manifests:** `argocd/` (in the scrape-stack repo itself)

---

## Services

| Service | Image |
|---|---|
| browserless | `browserless/chrome:latest` |
| request-auth-server | `dwilson2547/request-auth-server:latest` |
| request-auth-api | `dwilson2547/request-auth-api:latest` |
| request-auth-ui | `dwilson2547/request-auth-ui:latest` |
| webcache | `dwilson2547/webcache:latest` |
| imgcache | `dwilson2547/imgcache:latest` |
| filecache | `dwilson2547/filecache:latest` |
| vidcache | `dwilson2547/vidcache:latest` |
| cache-browser-api | `dwilson2547/cache-browser-api:latest` |
| cache-browser-ui | `dwilson2547/cache-browser-ui:latest` |

---

## Environments

| Environment | Branch | Namespace | Domain | Postgres |
|---|---|---|---|---|
| prod | `main` | `scrape-stack` | `scrapestack.local` | `postgres.postgres.svc.cluster.local` |
| dev | `dev` | `scrapestack-dev` | `scrapestack-dev.local` | `postgres-dev.postgres.svc.cluster.local` |

Values files: `helm/scrape-stack/values.yaml` (prod), `helm/scrape-stack/values-dev.yaml` (dev).

---

## Deploying Changes

For Helm chart or values changes:
```bash
git add ... && git commit -m "..." && git push
```
ArgoCD auto-syncs (`prune: true`, `selfHeal: true`).

For image updates — build and push from the relevant service repo, then the rollout happens
automatically on next sync (all images use `imagePullPolicy: Always` in dev;
update the image tag in values.yaml for prod).

---

## ArgoCD App Manifests

The ArgoCD apps live in `argocd/` within the scrape-stack repo:
- `argocd/scrape-stack.yaml` → prod
- `argocd/scrape-stack-dev.yaml` → dev

These must be applied manually when changed — ArgoCD does not manage its own Application CRs:
```bash
kubectl apply -f argocd/scrape-stack-dev.yaml
kubectl apply -f argocd/scrape-stack.yaml
```

---

## Secrets

Never committed. Apply manually before or after registering the ArgoCD app (it will retry):
```bash
kubectl apply -f example-secrets/  # fill in real values first
```

---

## Adding a New Service

1. Add the Helm templates under `helm/scrape-stack/templates/`
2. Add image and config values to `values.yaml` and `values-dev.yaml`
3. Commit and push — ArgoCD deploys automatically

---

## Rules

- Never `kubectl apply` Helm-managed resources — git push is the deploy mechanism
- ArgoCD app manifests (`argocd/*.yaml`) require both git push AND manual `kubectl apply` when changed
- Never commit real secret values
- Scrape-stack is independent of gyopart but both depend on the same postgres and cluster infrastructure from cluster_config
