# Copilot Instructions

## Source of truth

This repository is the source of truth for custom skills.

- Update files in `~/documents/workspace/SKILLS/`
- Do **not** edit `~/.agents/skills/` directly
- Do **not** edit `~/.claude/skills/` directly

Those installed skill paths are symlinks into this repository and should be treated as generated
install locations, not authoring locations.

## After changing skills

After adding, renaming, moving, or deleting skills in this repository, re-run:

```bash
cd ~/documents/workspace/SKILLS
./install_skill_symlinks.sh
```

Use `./install_skill_symlinks.sh --dry-run` first if you want to preview link changes.

## Project-backed skills

Some skills live inside larger project repositories vendored into this repo, for example:

- `ai_notes_server`
- `context-store`
- `ai_tool_docs`

For those skills, update the files under their paths inside this repository, not any older copy
outside `SKILLS/`.

## Editing rule

If a change is needed and both the `SKILLS/` repo path and an installed path are visible, always
edit the `SKILLS/` repo path.
