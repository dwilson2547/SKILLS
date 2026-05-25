#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <todo-store host or full API URL>" >&2
  echo "Examples:" >&2
  echo "  $0 todo.example.com" >&2
  echo "  $0 https://todo.example.com/api" >&2
  exit 1
fi

input="$1"

if [[ "$input" == http://* || "$input" == https://* ]]; then
  api_url="${input%/}"
else
  host="${input#https://}"
  host="${host#http://}"
  host="${host%/}"
  api_url="http://${host}/api"
fi

shell_rc="${SHELL_RC:-$HOME/.bashrc}"
export_line="export TODO_STORE_API_URL=\"${api_url}\""
tmp_file="$(mktemp)"

if [[ -f "$shell_rc" ]]; then
  awk -v line="$export_line" '
    BEGIN { replaced = 0 }
    /^export TODO_STORE_API_URL=/ {
      if (!replaced) {
        print line
        replaced = 1
      }
      next
    }
    { print }
    END {
      if (!replaced) {
        print line
      }
    }
  ' "$shell_rc" > "$tmp_file"
else
  printf '%s\n' "$export_line" > "$tmp_file"
fi

mv "$tmp_file" "$shell_rc"
echo "Updated ${shell_rc} with TODO_STORE_API_URL=${api_url}"
echo "Run: source ${shell_rc}"
