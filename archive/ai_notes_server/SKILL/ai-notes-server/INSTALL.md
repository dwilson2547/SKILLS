# Installing the notes CLI

Run the following to install. You'll be prompted for the server URL — press Enter to keep the default.

```bash
read -p "Notes API URL [http://localhost:8000]: " NOTES_URL
NOTES_URL=${NOTES_URL:-http://localhost:8000}

cp ~/.claude/skills/ai-notes-server/notes.py ~/.local/bin/notes
chmod +x ~/.local/bin/notes

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$NOTES_URL" != "http://localhost:8000" ]; then
  echo "export NOTES_API_URL=\"$NOTES_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
notes --help
```
