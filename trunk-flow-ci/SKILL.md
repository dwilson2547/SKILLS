---
name: trunk-flow-ci
description: 'Add or update GitHub Actions CI for a service or Helm chart following the trunk-flow pattern. Use when the user asks to add CI, set up GitHub Actions, add a workflow, or wire up a build and publish pipeline.'
---

# Trunk-Flow CI

Single `main` branch. PRs are the gate — tests and build run on PR open/update, image publish
runs on merge to main. Each service owns its own workflow file.

Reference implementations: `scrape_stack/services/*/github/workflows/ci.yml`

---

## Secrets Required

All workflows use the same two Docker Hub secrets (pre-configured at the repo or org level):
- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

---

## Service CI — `ci.yml`

One per service, at `.github/workflows/ci.yml` within the service directory (or at the repo
root for single-service repos).

```yaml
name: <service>-ci

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  changes:
    runs-on: ubuntu-latest
    outputs:
      service: ${{ steps.filter.outputs.service }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: dorny/paths-filter@v3
        id: filter
        with:
          filters: |
            service:
              - 'app/**'
              - 'tests/**'
              - 'requirements*.txt'
              - 'Dockerfile'
              - 'main.py'
              - 'docker-compose.yml'
              - '.github/workflows/**'

  pr-tests:
    if: github.event_name == 'pull_request' && needs.changes.outputs.service == 'true'
    needs: changes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -f Dockerfile -t <service>:ci .

  publish-image:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main' && needs.changes.outputs.service == 'true'
    needs: changes
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_TOKEN }}
      - id: tags
        run: |
          echo "sha_tag=sha-${GITHUB_SHA::12}" >> "$GITHUB_OUTPUT"
          echo "date_tag=$(date -u +%Y%m%d).${GITHUB_RUN_NUMBER}" >> "$GITHUB_OUTPUT"
      - uses: docker/build-push-action@v6
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: |
            ${{ secrets.DOCKERHUB_USERNAME }}/<service>:${{ steps.tags.outputs.sha_tag }}
            ${{ secrets.DOCKERHUB_USERNAME }}/<service>:${{ steps.tags.outputs.date_tag }}
            ${{ secrets.DOCKERHUB_USERNAME }}/<service>:latest
```

**Adapt the `paths-filter` block** to match the actual source layout of the service.
For Go services, replace `requirements*.txt`/`main.py` with `go.mod`/`go.sum`/`*.go`.

**Add a test step** in `pr-tests` if the service has a test suite:
```yaml
      - name: Run tests
        run: <test command>
```

---

## Helm CI — `helm-ci.yml`

For repos with a Helm chart. Lives at `.github/workflows/helm-ci.yml` in the repo root.

```yaml
name: helm-ci

on:
  pull_request:
    branches: [main]
    paths:
      - 'helm/<chart-name>/**'
      - '.github/workflows/helm-ci.yml'
  push:
    branches: [main]
    paths:
      - 'helm/<chart-name>/**'
      - '.github/workflows/helm-ci.yml'

permissions:
  contents: read

jobs:
  lint-and-package:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
        with:
          version: v3.15.2
      - name: Helm lint
        run: helm lint helm/<chart-name>
      - name: Helm package
        run: helm package helm/<chart-name> --destination /tmp/helm-dist

  publish-oci:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: lint-and-package
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/setup-helm@v4
        with:
          version: v3.15.2
      - name: Extract chart version
        id: chart
        run: |
          echo "version=$(awk '/^version:/{print $2}' helm/<chart-name>/Chart.yaml)" >> "$GITHUB_OUTPUT"
      - name: Login to Docker Hub registry
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
        run: echo "$DOCKERHUB_TOKEN" | helm registry login -u "$DOCKERHUB_USERNAME" --password-stdin docker.io
      - name: Fail if chart version already exists
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
        run: |
          if helm show chart "oci://docker.io/${DOCKERHUB_USERNAME}/<chart-name>" --version "${{ steps.chart.outputs.version }}" >/dev/null 2>&1; then
            echo "Chart version ${{ steps.chart.outputs.version }} already exists — bump Chart.yaml version before merging."
            exit 1
          fi
      - name: Package and push chart
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
        run: |
          helm package helm/<chart-name> --destination /tmp/helm-dist
          helm push "/tmp/helm-dist/<chart-name>-${{ steps.chart.outputs.version }}.tgz" "oci://docker.io/${DOCKERHUB_USERNAME}"
```

**Helm chart versions must be bumped in `Chart.yaml` before merging** — the workflow fails if
the version already exists in the OCI registry, preventing accidental overwrites.

---

## Image Tag Convention

Every published image gets three tags:
- `sha-<12-char git sha>` — exact build traceability
- `<YYYYMMDD>.<run_number>` — human-readable timeline
- `latest` — always points to the most recent main build

---

## Rules

- One `ci.yml` per service — do not share workflow files across services
- Path filtering is required — CI should not run when unrelated files change
- PR job builds but never pushes — publish only on merge to main
- Helm chart version must be bumped before merge — the CI enforces this
- Never hardcode Docker Hub username — always use `${{ secrets.DOCKERHUB_USERNAME }}`
