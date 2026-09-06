# Installing workman

Run the following to install the CLI:

```bash
read -p "Work Manager API URL [http://localhost:8010]: " WORKMAN_URL
WORKMAN_URL=${WORKMAN_URL:-http://localhost:8010}

cp ~/.claude/skills/work-manager/workman.py ~/.local/bin/workman
chmod +x ~/.local/bin/workman

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$WORKMAN_URL" != "http://localhost:8010" ]; then
  echo "export WORKMAN_API_URL=\"$WORKMAN_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
workman --help
workman projects
```

## Updating the URL later

Use the helper script:

```bash
bash ~/.claude/skills/work-manager/../../../scripts/set-api-url.sh <host-or-url>
source ~/.bashrc
```
