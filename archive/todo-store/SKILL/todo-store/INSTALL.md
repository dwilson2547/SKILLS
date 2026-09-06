# Installing the todo CLI

Run the following to install. Press Enter to keep the default URL.

For the cluster deployment, use `http://todo.ai-services.local/api`.

```bash
read -p "Todo Store API URL [http://localhost:8003]: " TODO_STORE_URL
TODO_STORE_URL=${TODO_STORE_URL:-http://localhost:8003}

cp ~/.claude/skills/todo-store/todo.py ~/.local/bin/todo
chmod +x ~/.local/bin/todo

if ! grep -q 'local/bin' ~/.bashrc; then
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
fi

if [ "$TODO_STORE_URL" != "http://localhost:8003" ]; then
  echo "export TODO_STORE_API_URL=\"$TODO_STORE_URL\"" >> ~/.bashrc
fi

source ~/.bashrc
```

Verify it works:

```bash
todo --help
```
