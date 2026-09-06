# Installing the docs CLI

Run the following to install. Press Enter to keep the default URL.

```bash
read -p "Tool Docs API URL [http://localhost:8002]: " DOCS_URL
DOCS_URL=${DOCS_URL:-http://localhost:8002}

mkdir -p ~/.local/bin
cp ~/.claude/skills/ai-tool-docs/docs.py ~/.local/bin/docs
chmod +x ~/.local/bin/docs

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$DOCS_URL" != "http://localhost:8002" ]; then
  echo "export DOCS_API_URL=\"$DOCS_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
docs --help
docs sources
```
