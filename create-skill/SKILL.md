---
name: create-skill
description: 'Create a new skill in the user''s SKILLS repo. Use when the user asks to create a skill, build a skill, or add a skill to their setup.'
---

# Create Skill

## Procedure

1. Determine the skill name in kebab-case
2. Create `<skill-name>/SKILL.md` under `/home/daniel/documents/workspace/SKILLS`
3. Write the file using the template below
4. Run `./install_skill_symlinks.sh` from the SKILLS repo root
5. Commit in the SKILLS repo

## SKILL.md Template

```markdown
---
name: <skill-name>
description: '<one-line trigger description>'
---

# <Title>

<content>
```

## Rules

- The `description` field is what the agent runtime uses to decide when to invoke the skill — write it precisely
- Always commit to `/home/daniel/documents/workspace/SKILLS`, never to the project repo
- Always run `./install_skill_symlinks.sh` after creating the file — without it the skill won't be linked into `~/.claude/skills` or `~/.agents/skills`
