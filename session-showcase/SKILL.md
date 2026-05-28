---
name: session-showcase
description: 'Generate a structured showcase document from the current session checkpoints and summary. Use when the user asks to document the session, create a session summary, write up what was accomplished, or produce a shareable record of the engineering work done.'
---

# Session Showcase

Generates a polished `docs/session_showcase_<YYYY_MM>.md` document from the current session's
checkpoints and in-context history. The result is a task-by-task record of what was requested
and what was delivered — suitable for sharing with teammates or stakeholders.

---

## Procedure

### 1. Locate the session folder

The session folder is at:

```
/home/daniel/.copilot/session-state/<session-id>/
```

The session ID is in the `SESSION_CONTEXT` provided to you. Read:

- `checkpoints/index.md` — table of all checkpoints with filenames
- All checkpoint `.md` files listed there (read them all in parallel)

Also use the in-context session summary if one was injected at the start of the conversation.

### 2. Determine the project root and docs path

Identify the project being worked on from the session folder and current working directory.
Check whether `<project-root>/docs/` exists. Create it if missing. The output file goes at:

```
<project-root>/docs/session_showcase_<YYYY_MM>.md
```

Use the current month/year for the filename suffix (e.g. `session_showcase_2026_05.md`).
If a file with that name already exists, append `_2` (or the next available suffix).

### 3. Extract the narrative from checkpoints

From the checkpoints and summary, compile:

- **What was already in place** at the start of the session (baseline state)
- **Each major task** in chronological order:
  - The user's original request (quote or paraphrase in plain English)
  - What the agent actually did (key decisions, files created/modified, tools used, problems solved)
  - The concrete outcome

A "major task" is a meaningful request that produced a visible result — a feature built,
a bug fixed, a deployment made, an investigation completed. Collapse minor back-and-forth
(clarifying questions, retries) into the task it belongs to. Do not create a separate entry
for every message.

### 4. Write the document

Use this structure:

```markdown
# <Project Name> — AI-Assisted Engineering Session Showcase
**<Month Year> · GitHub Copilot CLI (<model name>)**

---

## What Is This?

<2–4 sentence description of the project and what this session accomplished, written for
someone who has never seen the repo. Mention the key technologies involved.>

---

## What Was Already in Place at Session Start

- <bullet per baseline item>

---

## Task 1 — <Short Title>

**Request:** *"<User's words or a close paraphrase>"*

**What happened:**
- <What the agent investigated, decided, built, or fixed — enough detail to be meaningful>
- <Key files created or modified with a brief note on what each does>
- <Any interesting problems encountered and how they were resolved>

**Outcome:** <One sentence stating the concrete result.>

---

## Task 2 — ...

(repeat for each major task)

---

## Summary of Infrastructure Built

| Component | Technology | Notes |
|---|---|---|
| <row per significant piece of the stack> |

## Commits in This Session

| Hash | Description |
|---|---|
| <short hash> | <commit message> |

---

*Document generated <YYYY-MM-DD>. Repository: `<owner/repo>`.*
```

**Tone and content rules:**

- Write for a technical audience that does not know this project — be specific about technologies
- Lead each task with the user's plain-English request to make it clear this was conversational
- Emphasise *what the agent did autonomously* — investigation, decision-making, debugging,
  deployment — not just what files changed
- Commits table: include all commits from the session. Pull from checkpoint `work_done` sections.
  If no hashes are available, omit the table rather than guessing.
- Keep the infrastructure summary table to meaningful components only (not every config file)
- Do not pad with filler. Each task entry should be dense and informative.

### 5. Commit and push

```bash
cd <project-root>
git add docs/session_showcase_<YYYY_MM>.md
git commit -m "add session showcase document for <Month Year>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

Report the file path and confirm the push succeeded.
