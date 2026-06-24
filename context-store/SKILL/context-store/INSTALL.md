# Installing the context CLI

Run the following to install. Press Enter to keep the default URL.

```bash
read -p "Context Store API URL [http://localhost:8001]: " CONTEXT_STORE_URL
CONTEXT_STORE_URL=${CONTEXT_STORE_URL:-http://localhost:8001}

cp ~/.claude/skills/context-store/context.py ~/.local/bin/context
chmod +x ~/.local/bin/context

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$CONTEXT_STORE_URL" != "http://localhost:8001" ]; then
  echo "export CONTEXT_STORE_API_URL=\"$CONTEXT_STORE_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
context --help
```
