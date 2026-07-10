---
name: workspace-conventions
description: 'Governs structure and knowledge capture for the workspace superrepo. Use when working anywhere under the workspace repo: deciding where a new project/file/chart goes, naming or placing something, classifying a project by domain, or capturing/recalling reusable knowledge (repo-native notes via meta/bin/wsnote). Defers the full spec to the workspace-root CONVENTIONS.md.'
---

# Workspace Conventions

The operating manual for the workspace superrepo. The authoritative spec is **`CONVENTIONS.md` at
the workspace root** — read it when a placement/structure question is non-obvious. This skill is
the short, always-applied behavioral layer on top of it.

> Portable on purpose: this skill plus the root `CLAUDE.md`/`AGENTS.md` travel with the workspace
> repo, so any agent on any clone inherits these rules without machine-specific setup.

---

## Placement (when creating or moving anything)

- **One domain per project, chosen by purpose, not implementation.** A parts scraper is
  `automotive` (what it's for), not `web-scrapers` (how it's built). The domain list is **closed** —
  see the taxonomy table in `CONVENTIONS.md` §4; do not invent a new domain without editing that
  table.
- **`kebab-case`** for every domain and project name.
- **Submodule vs. plain folder** — submodule if it can stand up on its own (a service, app, lib,
  tool with its own lifecycle); plain folder for reference material and one-offs with no
  independent lifecycle. (§2)
- **Domain folders are never submodules.** A category is a plain folder. Nesting submodules is
  allowed *only* to model a real composite system you run — one with its own `helm/`/compose whose
  children have no independent home (e.g. `gyopart`). "Is it a thing you run?" is the test. (§1, §1a)
- **No `projects/` domain.** Scale is not a folder. Record it as a `tier:` marker in the project's
  README frontmatter: `system` | `project` | `experiment` | `reference`. (§4a)
- **Cross-cutting projects get one folder home (primary purpose) + secondary domains in note
  frontmatter (`domains:`).** CAN/DBC lives in `embedded`, its notes tagged `domains: automotive`. (§4b)
- **Helm:** self-deploying project → chart at `<project>/helm/<project>/`; cluster-wide/shared →
  `infra/cluster-config/`. (§6)

## Knowledge capture (the part that's been over- or under-used)

Knowledge lives **in the repo**, nothing else (§5). The old service stack (ai-notes-server,
context-store, workman notes/playbooks/todos) is retired — do not query or write to it.

1. **Domain-wide** → `<domain>/docs/` — `topics/` (long-form guidance), `patterns/`, and
   `notes/` (atomic frontmattered facts, managed by **`meta/bin/wsnote`**).
2. **Project-specific** → `<project>/docs/` (`issues/`, `decisions/`, `patterns/`, `notes/`).
   The issue-documentation skill already writes here. Backlogs are `TODO.md` at project root.
3. **Human prose** → the Obsidian vault. Generally not an agent target.

### Recall — before a task

Map the current working directory to its domain (via the §4 taxonomy). **If** the task is
non-trivial *and* domain-specific (scrapers, deploy/infra, embedded gotchas, known-tricky areas),
check that domain's knowledge first: skim `<domain>/docs/notes/README.md` (the one-line index),
or run `meta/bin/wsnote search <terms> --domain <domain>`. **Skip the lookup** for trivial or
cosmetic work (renames, formatting, one-line fixes) — not searching is the correct default there.

### Save — after a task

Save **at most one** note per task, and only when the work produced something reusable that passes
this gate:

> Would this change how a *future, similar* task is approached?

A discovered cross-site/cross-project pattern, a non-obvious toolchain gotcha, or an architectural
decision passes. A renamed variable, a routine fix, or anything findable in official docs fails —
do **not** save it. When saving:

- `meta/bin/wsnote add <domain-or-project-path> "<title>" "<2–5 sentence body>" --tags a,b`
  (add `--domains x,y` for secondary domains, §4b). It writes the file and updates the index.
- Long-form/structured content (headers, multi-step procedures) is a `topics/` doc, not a note —
  write the file directly and optionally add a pointer note.
- Prefer updating an existing note file over creating a near-duplicate; run
  `meta/bin/wsnote reindex` after hand-edits.
- Notes are repo files: they ship when committed, so commit them with the work.

This deliberately replaces freeform "is this worth saving?" judgment (which oscillates between
noisy and silent) with a structural gate keyed to the closed domain taxonomy.

## Conformance

When you touch a project, opportunistically bring it toward the §7 checklist (single domain folder,
kebab-case, README with `tier:`, `docs/` present, chart at `helm/<project>/`, start/kill scripts if
it's a runnable app/service/game, no stray cruft). Do not run a big-bang migration; `CONVENTIONS.md`
§8 tracks the deferred debt.

**New runnable projects (services, apps, games)** should ship their start/kill scripts from the
outset, not opportunistically — cheap to add up front, and saves re-deriving the launch incantation
every time you or an agent needs to manually test it.
