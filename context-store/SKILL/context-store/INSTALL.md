# Installing the playbooks CLI

Run the following to install. Press Enter to keep the default URL.

```bash
read -p "Playbooks API URL [http://localhost:8001]: " PLAYBOOKS_URL
PLAYBOOKS_URL=${PLAYBOOKS_URL:-http://localhost:8001}

cp ~/.claude/skills/playbooks/playbooks.py ~/.local/bin/playbooks
chmod +x ~/.local/bin/playbooks

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$PLAYBOOKS_URL" != "http://localhost:8001" ]; then
  echo "export PLAYBOOKS_API_URL=\"$PLAYBOOKS_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
playbooks --help
```
