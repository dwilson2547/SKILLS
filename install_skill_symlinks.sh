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

Skills are auto-discovered from top-level folders that contain SKILL.md.
Retired skills live in archive/ and are deliberately not discovered.
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
