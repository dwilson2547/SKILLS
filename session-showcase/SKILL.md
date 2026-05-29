---
name: session-showcase
description: 'Generate a structured showcase document from a session — current or historical. Use when the user asks to document the session, create a session summary, write up what was accomplished, or produce a shareable record of the engineering work done. The user may ask for the current session or for a specific past/historical session they have re-opened.'
---

# Session Showcase

Generates a polished `session_showcase_<YYYY_MM>.md` document from a session's checkpoints
and in-context history. The result is a task-by-task record of what was requested and what
was delivered — suitable for sharing with teammates or stakeholders.

The user may ask you to document:
- **The current session** — standard case, use checkpoints + in-context history
- **A historical session** — a past session the user has re-opened or is reviewing; the
  full conversation is already in context. Do not treat this as the current session.
  Derive date and project from the conversation content, not from today's date.

---

## Procedure

### 1. Determine session type and locate data

**Ask yourself:** is the user asking to document work that happened *in this conversation*
(historical re-open) or work from a separate CLI session with checkpoints?

#### A — VS Code Chat sessions (no checkpoints)

VS Code chat sessions do **not** produce `.copilot/session-state` checkpoint files.
For these sessions the entire record is the conversation already in context.

Data sources (in priority order):
1. **In-context conversation** — the primary source. Read the full exchange to identify
   every task, tool call, file created/modified, and outcome.
2. **VS Code debug log** (if needed for confirmation):
   `~/.vscode-server/data/User/workspaceStorage/<workspace-id>/GitHub.copilot-chat/debug-logs/<session-id>/main.jsonl`
   The session ID appears in the `VSCODE_TARGET_SESSION_LOG` template variable when available.

When documenting a **historical** VS Code chat session: the conversation content is already
loaded. Work from it directly — do not attempt to load checkpoints that do not exist.

#### B — CLI sessions (with checkpoints)

The session folder is at:

```
/home/daniel/.copilot/session-state/<session-id>/
```

The session ID is in the `SESSION_CONTEXT` provided to you. Read:

- `checkpoints/index.md` — table of all checkpoints with filenames
- All checkpoint `.md` files listed there (read them all in parallel)

Also use the in-context session summary if one was injected at the start of the conversation.

### 2. Determine the docs path

All session showcases are saved to the central `cluster_config` repository regardless of
which project was worked on during the session:

```
/home/daniel/documents/workspace/cluster_config/docs/session_showcase_<YYYY_MM>.md
```

Use the month/year **when the work was done** for the filename suffix — not necessarily
today's date. For historical sessions derive the date from the conversation content
(timestamps, file recon dates, session context). If ambiguous, ask.

If a file with that name already exists, append `_2`, `_3`, etc. (next available suffix).

### 3. Extract the narrative

From the checkpoints / conversation, compile:

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
**<Month Year> · GitHub Copilot <Chat|CLI> (<model name>)**

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
- Commits table: include all commits from the session. Pull from checkpoint `work_done` sections
  (CLI) or from git log evidence in the conversation (chat). If no hashes are available, replace
  the table with a plain note explaining why (e.g. "No commits were made — documentation files
  only" or "Session was a VS Code chat with no checkpoint commit tracking").
- Keep the infrastructure summary table to meaningful components only (not every config file)
- Do not pad with filler. Each task entry should be dense and informative.

### 5. Commit and push

```bash
cd /home/daniel/documents/workspace/cluster_config
git add docs/session_showcase_<YYYY_MM>.md
git commit -m "add session showcase document for <Month Year>

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"
git push
```

Report the file path and confirm the push succeeded.
