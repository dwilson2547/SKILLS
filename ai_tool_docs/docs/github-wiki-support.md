# GitHub Wiki Support

Added 2026-05-24. Describes how wiki repos are indexed and what was tried before arriving at the current approach.

## How to Add a Wiki Source

Enter the repo as `owner/repo.wiki` (e.g. `tmux/tmux.wiki`). The branch field is ignored — the sync always clones HEAD. Leave `file_glob` as `*.md` and `docs_folders` empty.

## How It Works

Wiki repos are real git repositories hosted at `https://github.com/{owner}/{repo}.wiki.git` but are **not** exposed through the standard GitHub REST API. The sync uses two git operations:

1. **`git ls-remote {clone_url} HEAD`** — fetches the HEAD SHA with negligible data transfer. If the SHA matches `last_commit_sha` in the DB, the sync exits immediately.
2. **`git clone --depth=1 --quiet {clone_url} {tmpdir}`** — shallow clone into a temp directory when a change is detected. The clone is deleted with `rm -rf` in a `finally` block regardless of success or failure.

The `GITHUB_TOKEN` env var is embedded in the clone URL when present so authenticated clones work without interactive prompts.

`git` must be present in the API container — it is installed via `apt-get install -y git` in the Dockerfile.

## What Didn't Work

### `/repos/{owner}/{repo}.wiki` REST endpoints

All standard repo-level REST endpoints return **404** for wiki repos:

- `GET /repos/tmux/tmux.wiki` — 404 (used for branch auto-detection)
- `GET /repos/tmux/tmux.wiki/commits?sha=master&per_page=1` — 404 (used to get HEAD SHA)

The wiki repo simply doesn't exist as a first-class resource in the GitHub REST API.

### `GET /repos/{owner}/{repo}/wiki/pages`

GitHub's wiki pages REST endpoint returns **404 on github.com**. This endpoint is documented but is only available on **GitHub Enterprise Server / GitHub AE**, not the public github.com API.

### Raw content URLs

`https://raw.githubusercontent.com/wiki/{owner}/{repo}/{page}.md` was considered for per-page downloads but abandoned because it still requires a separate mechanism to enumerate which pages exist — and any enumeration path via the REST API hits the same 404 wall.

## Why Not Sparse Checkout

`git clone --filter=blob:none --no-checkout` + per-blob `git cat-file` was considered to avoid downloading unchanged file content. For wiki repos (pure markdown, typically a few dozen files totalling well under 1 MB) the overhead of a full shallow clone is negligible and the implementation is significantly simpler.
