---
name: feature-development
description: 'The default workflow for building, changing, or fixing code. Use for any implementation request — a bug fix, a config change, adding a field or endpoint, a refactor, or a new component. Determines scope from the code itself rather than from the request, then either executes directly or escalates for agreement first. Trigger phrases: build, implement, add, fix, change, update, refactor, wire up, make it do X. Defer to a domain skill when one fits: ui-development or ui-repair-loop for UI work, dockerfile-creation or docker-compose-creation for containers, alembic-migrations for schema migrations, scraper-development-skill for scrapers. Use this when no domain skill applies.'
---

# Feature Development

One workflow for implementation work. It does **not** assume the task is small — it establishes
scope from the code first, and raises a hand before starting anything large.

The bias is toward doing the work: no spec documents, no brainstorming phase, no validation theatre
for a config change. Ceremony is earned by scope, not applied by default.

---

## Step 1 — Establish scope from the code

Read the files the change touches. Then write down, explicitly, **the list of files you will
modify or create**.

Do this before writing any code, and before forming a view on how big the task is. An estimate made
from the request alone is a guess made with the least information you will ever have, and it is
consistently wrong in the direction of "this is small." The list is also what step 4 checks the
finished work against, so it has to be written down, not held in your head.

**If that list runs past a handful of files, or the change crosses a module, schema, or public
interface boundary — say so and get agreement before writing code.** Name what makes it large and
describe the approach in a few sentences. That is the whole escalation: a paragraph in the
conversation, not a spec document and not subagents.

If you discover mid-implementation that this applies, stop and raise it then. That is not a
failure; continuing quietly is.

## Step 2 — Implement

Write the code directly. No intermediate documents, no staging work in notes or handoff docs.

Do the work yourself. Delegating to a subagent costs a cold start and re-derivation of context you
already hold — only worth it for genuinely independent, parallelisable work.

## Step 3 — Verify what the change touches

Run the check that actually exercises the change: tests, a build, a smoke test, or driving the app.

**Verify the change's surroundings, not just the lines you wrote.** The recurring failure is
checking that the new code works while never checking what it sits next to — the caller, the
sibling config, the hook it shadows, the integration it feeds. Name explicitly what you verified
and what you did not.

## Step 4 — Completion checklist

Do not report the task complete until every line below is true. State each one:

1. **Every file in the step-1 list** is either modified as intended, or explicitly named as dropped
   and why.
2. **The step-3 check ran**, and you can name it and its actual result — not "should work."
3. **Nothing crept in beyond what step 1 scoped.** If the change grew, say so.
4. **The working tree is committed** (CONVENTIONS.md §9 — commit even if unfinished; a WIP commit
   beats a dirty tree) and pushed.
5. **Documentation closure**, where it applies:
   - `docs/issues/YYYY_MM_DD_<slug>.md` for any error that needed non-obvious debugging, or any
     dependency/config/integration behaviour that was not evident from the code.
   - A note via `wsnote add <scope> "<title>" "<body>" --tags a,b`, carrying `--source` when it
     distils a longer doc. One note maximum, and only if it would change how a future similar task
     is approached.
6. **State what you did not do** — untested paths, deferred cases, assumptions made.

A single focused edit with no debugging and no surprises can skip item 5, and only item 5.
