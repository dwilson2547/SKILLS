#!/usr/bin/env bash
# Optional: sets up the local embedding backend for `doc-indexer search`.
#
# doc-indexer itself is pure stdlib — `index --no-embed` and `find` need
# nothing from this script. Run this once to enable semantic `search` (and
# embedding during `index`): it creates a .venv next to this script and
# installs fastembed into it. doc-indexer auto-detects and re-execs into
# that venv, so no activation or PATH changes are needed afterwards.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements-embed.txt

echo "done. 'doc-indexer search' and embedding-enabled 'index' now work."
echo "the model itself (~65MB) downloads on first use, cached under"
echo "\$DOC_INDEXER_MODEL_CACHE or ~/.cache/doc-indexer/models."
