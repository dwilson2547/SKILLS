#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENTS_DIR="${HOME}/.agents/skills"
CLAUDE_DIR="${HOME}/.claude/skills"
DRY_RUN=false

usage() {
  cat <<'EOF'
Usage: ./install_skill_symlinks.sh [--dry-run]

Creates skill symlinks from this SKILLS repo into:
  ~/.agents/skills
  ~/.claude/skills

Standalone skills are auto-discovered from top-level folders that contain SKILL.md.
Project-backed skills with nested SKILL directories are mapped explicitly.
EOF
}

log() {
  printf '%s\n' "$*"
}

link_path() {
  local target="$1"
  local dest="$2"

  if [[ -L "$dest" || -f "$dest" ]]; then
    if [[ "$DRY_RUN" == true ]]; then
      log "would replace $dest -> $target"
    else
      rm -f "$dest"
      ln -s "$target" "$dest"
      log "linked $dest -> $target"
    fi
    return
  fi

  if [[ -e "$dest" ]]; then
    log "skipping $dest (exists and is not a symlink)"
    return
  fi

  if [[ "$DRY_RUN" == true ]]; then
    log "would create $dest -> $target"
  else
    ln -s "$target" "$dest"
    log "linked $dest -> $target"
  fi
}

resolve_context_store_target() {
  local candidate
  for candidate in \
    "${SCRIPT_DIR}/context-store/SKILL/context-store" \
  do
    if [[ -f "${candidate}/SKILL.md" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  log "error: could not find a context-store skill folder under ${SCRIPT_DIR}/context-store/SKILL" >&2
  return 1
}

resolve_todo_store_target() {
  local candidate="${SCRIPT_DIR}/todo-store/SKILL/todo-store"
  if [[ -f "${candidate}/SKILL.md" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi

  log "error: could not find a todo-store skill folder under ${SCRIPT_DIR}/todo-store/SKILL" >&2
  return 1
}

main() {
  if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    usage
    exit 0
  fi

  if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
  elif [[ $# -gt 0 ]]; then
    usage >&2
    exit 1
  fi

  mkdir -p "$AGENTS_DIR" "$CLAUDE_DIR"

  declare -A skill_targets=()

  while IFS= read -r -d '' skill_dir; do
    skill_targets["$(basename "$skill_dir")"]="$skill_dir"
  done < <(find "$SCRIPT_DIR" -mindepth 1 -maxdepth 1 -type d -exec test -f "{}/SKILL.md" ';' -print0 | sort -z)

  skill_targets["ai-notes-server"]="${SCRIPT_DIR}/ai_notes_server/SKILL/ai-notes-server"
  skill_targets["ai-tool-docs"]="${SCRIPT_DIR}/ai_tool_docs/SKILL/ai-tool-docs"
  skill_targets["context-store"]="$(resolve_context_store_target)"
  if [[ -d "${SCRIPT_DIR}/todo-store" ]]; then
    skill_targets["todo-store"]="$(resolve_todo_store_target)"
  fi
  if [[ -d "${SCRIPT_DIR}/work-manager" ]]; then
    skill_targets["work-manager"]="${SCRIPT_DIR}/work-manager/SKILL/work-manager"
  fi

  for skill_name in $(printf '%s\n' "${!skill_targets[@]}" | sort); do
    target="${skill_targets[$skill_name]}"

    if [[ ! -f "${target}/SKILL.md" ]]; then
      log "skipping ${skill_name} (missing ${target}/SKILL.md)"
      continue
    fi

    link_path "$target" "${AGENTS_DIR}/${skill_name}"
    link_path "$target" "${CLAUDE_DIR}/${skill_name}"
  done
}

main "$@"
