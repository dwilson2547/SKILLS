---
name: workspace-conventions
description: 'Governs structure and knowledge capture for the workspace superrepo. Use when working anywhere under the workspace repo: deciding where a new project/file/chart goes, naming or placing something, classifying a project by domain, or capturing/recalling reusable knowledge. Defers the full spec to the workspace-root CONVENTIONS.md and the notes CLI mechanics to the ai-notes-server skill.'
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
- **Cross-cutting projects get one folder home (primary purpose) + secondary-domain tags in the
  notes layer.** CAN/DBC lives in `embedded`, tagged `automotive`. (§4b)
- **Helm:** self-deploying project → chart at `<project>/helm/<project>/`; cluster-wide/shared →
  `infra/cluster-config/`. (§6)

## Knowledge capture (the part that's been over- or under-used)

Three homes, nothing else (§5):

1. **Per-project** → `<project>/docs/` (`issues/`, `decisions/`, `patterns/`). Project-specific.
   The issue-documentation skill already writes here.
2. **Human prose** → the Obsidian vault. Generally not an agent target.
3. **Cross-cutting reusable** → the AI notes server, **namespaced by domain**. Use the
   `ai-notes-server` skill for CLI mechanics; this skill governs *when* and *what*.

### Recall — before a task

Map the current working directory to its domain (via the §4 taxonomy). **If** the task is
non-trivial *and* domain-specific (scrapers, deploy/infra, embedded gotchas, known-tricky areas),
search notes scoped to that domain first. **Skip the lookup** for trivial or cosmetic work
(renames, formatting, one-line fixes) — not searching is the correct default for those.

### Save — after a task

Save **at most one** note per task, and only when the work produced something reusable that passes
this gate:

> Would this change how a *future, similar* task is approached?

A discovered cross-site/cross-project pattern, a non-obvious toolchain gotcha, or an architectural
decision passes. A renamed variable, a routine fix, or anything findable in official docs fails —
do **not** save it. When saving:

- Namespace by domain: `<domain>/<slug>`.
- Tag with the domain, any **secondary domains** (§4b), and `tier` if relevant.
- Prefer updating an existing note over creating a near-duplicate.

This deliberately replaces freeform "is this worth saving?" judgment (which oscillates between
noisy and silent) with a structural gate keyed to the closed domain namespace.

## Conformance

When you touch a project, opportunistically bring it toward the §7 checklist (single domain folder,
kebab-case, README with `tier:`, `docs/` present, chart at `helm/<project>/`, no stray cruft). Do
not run a big-bang migration; `CONVENTIONS.md` §8 tracks the deferred debt.
