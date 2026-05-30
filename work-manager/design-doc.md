# Work Manager — Goals, Scope & Design

## Problem Statement

The current agent workflow toolchain consists of four independent services (notes, context-store, tool-docs, todo-store) running eight Docker images. Each service was built with a focused purpose but together they produce a fragile chain-of-pointers model where agents must perform multiple sequential queries before they have enough context to begin meaningful work. This creates several compounding failure modes:

- Agents override explicit prompts after reading globally-scoped notes
- Parent tasks marked complete while subtasks are partially done or undocumented
- Bots inherit stale or mismatched context from previous sessions
- No enforced definition of done at any work hierarchy level
- No unified interface for humans or agents to interact with the system

---

## Goals

1. Replace the four-service chain with a single unified work management layer
2. Provide agents a single-query "work brief" containing everything needed to execute a task
3. Enforce definition of done and testing strategy at every level of the work hierarchy
4. Prevent premature task completion by requiring explicit, verifiable acceptance criteria
5. Surface relevant notes and context automatically based on tag overlap, not global dumps
6. Preserve design documents as first-class objects linked to the tasks they inform
7. Reduce operational footprint from eight Docker images to a manageable minimum
8. Maintain fast iteration via export/import compatibility with existing services

---

## Non-Goals

- Replacing GitHub Issues or Jira for team-scale project tracking
- Real-time collaboration or multi-user concurrent editing
- Full-text search across all historical work (scoped semantic search is sufficient)
- Automated task execution (work-manager is a context and state layer, not an orchestrator)

---

## Architecture Overview

### Service Boundaries

Work Manager consolidates all four existing services into one:

```
work-manager/
  ├── Projects, Epics, Tasks, Subtasks     (replaces todo-store)
  ├── Notes                                 (replaces notes service)
  ├── Design Documents / Context Store      (replaces context-store)
  └── Tool Docs                             (replaces tool-docs, same engine)
```

### Backing Store

SQLite with sqlite-vec extension:

- Structured work items in relational tables
- Document content stored as text with vector embeddings for semantic search via sqlite-vec virtual tables
- Tag taxonomy shared across all document types enabling cross-type semantic joins
- No cross-service queries at agent runtime — all assembly happens server-side
- WAL mode enabled at connection time (`PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;`) for concurrent read/write behavior
- Consistent with existing AI services already running SQLite on PVCs in cluster
- **NFS caveat:** SQLite WAL mode uses shared memory-mapped files that do not work correctly over NFS. Ensure the backing PVC is iSCSI or block-device backed (democratic-csi), not an NFS share. Postgres should be substituted if only NFS-backed storage is available.

### Interfaces

- **REST API** — primary interface for all reads and writes
- **CLI** — agent-facing, designed for pipe-friendly single-command workflows
- **Web UI** — human-facing, minimal, read/write for all entity types

---

## Work Hierarchy

```
Project
  └── Epic
        └── Task
              └── Subtask
```

Every level carries the same core fields — definition of done, testing strategy, status, and acceptance criteria. No level can be marked complete unless all children are explicitly resolved.

### Completion Rules

- A **Subtask** is complete when its acceptance criteria are met and its testing strategy has been executed and documented
- A **Task** is complete only when all subtasks are complete and the task-level definition of done is satisfied independently
- An **Epic** is complete only when all tasks are complete and integration-level acceptance criteria are verified
- A **Project** is complete only when all epics are complete and end-to-end acceptance criteria are verified

Agents cannot mark a parent complete if any child is in a non-terminal state. The API enforces this — it is not advisory.

---

## Entity Schema

### Shared Fields (all levels)

```yaml
id: string
title: string
description: markdown
status: draft | in_progress | blocked | in_review | complete | abandoned
tags: string[]
created_at: timestamp
updated_at: timestamp

acceptance_criteria:
  - id: string
    description: string
    verified: boolean
    verified_at: timestamp
    verified_by: string        # agent id or human

definition_of_done:
  description: markdown        # what "complete" explicitly means for this item
  checklist:
    - item: string
      checked: boolean

testing_strategy:
  description: markdown        # how correctness is verified
  layers:
    - layer: unit | integration | e2e | manual | observability
      description: string
      status: pending | passed | failed | skipped
      notes: string

dependencies: string[]         # ids of blocking items
blocked_reason: string         # required if status is blocked
```

### Project-specific Fields

```yaml
design_docs: string[]          # ids of attached design documents
goal: string                   # one paragraph, human and agent readable
```

### Task / Subtask-specific Fields

```yaml
parent_id: string
context_snapshot: markdown     # embedded at creation time from design docs
relevant_notes: Note[]         # tag-filtered, embedded at brief generation time
estimated_effort: xs | s | m | l | xl
assignee: string
```

---

## Notes

Notes are short, scoped learnings — not session dumps or task descriptions.

### Rules

- Maximum 10 sentences — enforced server-side; submissions exceeding this limit are rejected with a validation error
- Must have at least one `scope` tag (e.g. `scope:tool:datadog`, `scope:domain:scraping`, `scope:service:registry`)
- Notes surface in task briefs only when scope tags overlap with task tags
- Notes are never queried globally by agents — only via tag-filtered task brief assembly
- If a note grows beyond its 10-sentence limit, it should become a design document

### Schema

```yaml
id: string
title: string
body: markdown                 # max 10 sentences
tags: string[]                 # must include at least one scope: tag
created_at: timestamp
updated_at: timestamp
```

---

## Design Documents & Tool Docs

Both use the same storage and retrieval engine. Ingestion source differs:

- **Design documents** — user-uploaded markdown or plain text
- **Tool docs** — sparse checkout of a GitHub repo, markdown files indexed automatically

### Retrieval

- TOC available without fetching full document
- Chunk-level retrieval by section heading
- Semantic search across all chunks via sqlite-vec virtual tables
- Chunks embedded into task context snapshots at task creation time (not at agent runtime)
- When a design document is updated, all embeddings for that document are recomputed and any task snapshots linked to that document are refreshed automatically — no embedding history is retained, as versioning old embeddings would complicate the import/export pattern without meaningful benefit

### Epic Linkage

Design documents are explicitly linked to epics by ID. Tag-overlap discovery is not used at the epic level — explicit linkage ensures agents receive only the documents that directly inform the work, not loosely-related documents that happen to share a tag.

---

## Sibling Task Status

The brief includes a one-line status summary for all sibling tasks (tasks sharing the same parent epic) so agents have immediate awareness of in-progress or blocked work before starting. This prevents duplicate effort and surfaces natural coordination points.

```
## Sibling Tasks
[TASK-40] Define OSM poly builder output format — complete
[TASK-41] Validate lap detection pipeline schema — in_progress
[TASK-43] Write migration tooling for Track v1 → v2 — pending
```

---

## Task Brief — Agent Interface

The primary agent-facing primitive. One CLI command returns a self-contained document.

```bash
workman task brief TASK-42
```

### Brief Contents

```
# Task: Define canonical Track schema [TASK-42]

Status: in_progress
Parent: EPIC-07 — Central Registry
Tags: component:registry, domain:geospatial, scope:schema

## Description
...

## Acceptance Criteria
[ ] Schema covers all fields required by lap detection pipeline
[ ] Schema covers all fields required by OSM poly builder
[ ] Avro definition committed to schema registry

## Definition of Done
All acceptance criteria checked. Schema deployed to dev environment.
At least one downstream service successfully validated against schema.
No open questions on field nullability or typing.

## Testing Strategy
- unit: Schema serialization/deserialization roundtrip test
- integration: Lap detection pipeline consumes schema without errors
- manual: Review against OSM poly builder output

## Context (from Design Doc: Registry Architecture v2, §Track Model)
...embedded chunk...

## Relevant Notes
[NOTE-14 | scope:domain:geospatial] When building geopolys from OSM ways, 
buffer centerline by nominal track width before treating as area polygon...

## Dependencies
Blocked by: TASK-38 (OSM poly builder output format finalized) ✓ complete
```

Agents receive complete context in one read. No follow-up queries required under normal conditions.

---

## Completion Enforcement

### API Behavior

`PATCH /tasks/{id}` with `status: complete` will be rejected if:

- Any acceptance criterion has `verified: false`
- Any testing strategy layer is in `pending` state without an explicit `skipped` status and skip reason
- Any subtask is not in a terminal state (`complete` or `abandoned`)
- `definition_of_done.checklist` contains unchecked items

### Agent Workflow Contract

Agents must:

1. Call `workman task brief {id}` before beginning work
2. Update subtask status to `in_progress` when starting
3. Mark each acceptance criterion verified individually as work progresses
4. Document testing strategy results before attempting completion
5. Call `workman task complete {id}` which validates server-side before accepting

Agents must not:

- Mark a parent complete before children are resolved
- Skip the testing strategy documentation step
- Assume a sibling or parent task is complete without querying its status


---

## Issue Documents

Issue documents are structured incident records produced when a bug or operational failure is found and resolved. They are first-class entities, not generic documents with a tag. They attach to tasks or epics by ID and surface automatically in task briefs when component tags overlap.

### Schema

```yaml
id: string
title: string
severity: sev1 | sev2 | sev3
status: open | resolved
tags: string[]                   # component and service tags for brief surfacing
linked_task_id: string           # task or epic this incident relates to
linked_runbook_ids: string[]     # runbooks created or used during resolution
sections:
  triage_steps: markdown
  root_cause: markdown
  resolution: markdown
  lessons_learned: markdown
created_at: timestamp
resolved_at: timestamp
```

### Rules

- Issue documents are first-class entities interactable via the same REST API and CLI as all other work items
- Every resolved issue must have all four sections completed before status can be set to `resolved`
- `lessons_learned` entries are candidates for promotion to Notes (scoped) or Runbook updates — this is a human decision, not automatic
- Linked runbooks are updated or created as a follow-on step after issue resolution

---

## Runbooks

Runbooks are living operational procedures for resolving known incidents. They are scoped to a service and category rather than to a project or epic — they exist for the lifetime of the service, not the lifetime of a work item.

Runbooks are explicitly not generic context-store documents with a playbook tag. The discoverability model is service-first: "what are all the runbooks for service X" rather than "find documents tagged runbook."

### Schema

```yaml
id: string
title: string
service: string                  # primary owning service e.g. "registry", "microk8s"
category: string                 # incident category e.g. "image-pull", "network", "storage"
version: int                     # incremented on meaningful revision
status: draft | active | deprecated
tags: string[]
sections:
  symptoms: markdown             # how to recognize this incident
  prerequisites: markdown        # what access or tools are needed before starting
  steps: markdown                # resolution procedure
  verification: markdown         # how to confirm the incident is resolved
  escalation: markdown           # what to do if steps do not resolve it
linked_issue_ids: string[]       # issues that informed or used this runbook
last_validated_at: timestamp     # when this runbook was last tested or reviewed
created_at: timestamp
updated_at: timestamp
```

### Rules

- Runbooks older than 90 days without a `last_validated_at` update are flagged as potentially stale
- Deprecated runbooks are retained for historical reference but excluded from active discovery
- `linked_issue_ids` links back to the original incident and any subsequent incidents resolved using this runbook — closing the loop between cause and procedure
- A runbook must reach `active` status before being surfaced in task briefs or issue documents

### CLI

```bash
# Service-scoped discovery
workman runbook list --service microk8s
workman runbook list --service registry --category network

# Full brief including linked issues
workman runbook brief RUNBOOK-12

# Flag as validated after review or successful use
workman runbook validate RUNBOOK-12
```

---

## Project Templates *(Stretch Goal)*

Project templates allow new projects to be instantiated with a pre-populated hierarchy of epics, tasks, subtasks, acceptance criteria, and definitions of done reflecting established conventions. Templates are system-defined — users select from a curated set at project creation time and do not author their own. The intent is that creating a new project from the `trunk-flow-ci` template, for example, immediately produces a fully planned epic/task/subtask tree covering all the work required to stand up CI for that project, ready to assign and execute.

### Use Cases

Examples of first-party templates:

- `trunk-flow-ci` — Git trunk-based flow with CalVer versioning, multi-registry publish pipeline, branch protection rules
- `otel-monitoring` — OpenTelemetry instrumentation, Grafana dashboard scaffold, alerting thresholds, runbook stubs
- `playwright-testing` — E2E test scaffold, CI integration, page object model structure, coverage reporting
- `k8s-service` — Helm chart scaffold, MetalLB config, health check endpoints, HPA config, PVC if needed
- `fastapi-service` — project layout, Dockerfile, schema validation, auth middleware stub, OpenAPI doc generation

### Template Schema

```yaml
id: string
name: string
description: string
version: string
variables:
  - key: string              # e.g. PROJECT_NAME, REPO_URL, SERVICE_NAME
    label: string
    type: string | enum | boolean
    required: boolean
    default: string
structure:
  epics:
    - title: string          # may reference {{VARIABLE_KEY}}
      description: markdown
      tasks:
        - title: string
          description: markdown
          acceptance_criteria:
            - description: string
          definition_of_done:
            description: markdown
            checklist:
              - item: string
          testing_strategy:
            layers:
              - layer: string
                description: string
          subtasks:
            - title: string
              description: markdown
```

### UI Flow

1. User selects "New Project" in the UI
2. UI presents a checklist of available templates
3. User selects one or more templates to compose into the project
4. UI renders a variable form derived from the union of selected template schemas
5. User fills in project-specific values and submits
6. Work-manager instantiates the full hierarchy with variables substituted
7. Project opens with all epics, tasks, and subtasks in `draft` status ready for review and assignment

### Composability

Multiple templates can be applied to a single project. Variable namespaces are per-template to avoid collision. A `k8s-service` + `otel-monitoring` + `playwright-testing` composition produces a project with all three epic trees merged under one project, which is the typical starting point for a new production service.

### Template Storage

Templates are versioned markdown documents with YAML frontmatter stored in a dedicated templates directory. They ship with the service and live in version control — diffable and updatable via normal file operations. There is no user-defined template path; all templates are system-managed and released with the service.

---

## Agent Workflow Vision

The intended operating pattern once work-manager is live:

1. A design document is ingested and linked to an epic — epics, tasks, and subtasks are created with acceptance criteria and definitions of done pre-populated from that design doc
2. An agent is told to pull the next item from work-manager; it calls `workman task next` (or a project-scoped variant) and receives a fully assembled brief
3. A `workman` skill explains the CLI contract and what agents are expected to do when interacting with the system
4. The agent works through the task, marking acceptance criteria verified as it goes
5. When the agent encounters a bug or incident, it creates an issue document via `workman issue create` and links it to the task — root cause, resolution, and lessons learned are filled in before the issue is resolved
6. When the agent discovers a reusable pattern or tooling behavior worth preserving, it saves a scoped note via `workman note add` with appropriate tags — future task briefs touching the same domain will surface it automatically
7. The agent cannot mark the task complete until all acceptance criteria are verified, testing strategy layers are documented, and no subtasks are unresolved — this is enforced by the API
8. Notes can also be queried independently; they are not only surfaced through task briefs

This closes the loop between planning, execution, incident management, and knowledge accumulation without requiring agents to orchestrate across multiple services.

---

## Migration from Existing Services

All four existing services expose export capability. Migration path:

1. Export all data from notes, context-store, tool-docs, todo-store
2. Map todo-store items to Tasks with empty acceptance criteria and definition-of-done (flagged for human review)
3. Import notes with scope tag normalization — notes without scope tags are flagged for review, not imported automatically
4. Import context-store documents as Design Documents
5. Re-index tool-docs via sparse checkout against existing repo list
6. Validate via CLI that all cross-references resolve

Migration does not require existing services to be decommissioned first — work-manager runs alongside until validated.

---

## Operational Footprint

Target: two Docker images

| Image | Purpose |
|---|---|
| `work-manager-api` | REST API, brief assembly, completion enforcement |
| `work-manager-ui` | Web UI |

SQLite database file lives on a PVC mounted into the API container — no separate database container required.

CLI is a binary distributed separately, no container required.

---

## Observability

Work-manager exports OpenTelemetry traces and metrics via OTLP gRPC to the existing cluster collector. No new infrastructure required.

### Instrumentation

- `opentelemetry-instrumentation-fastapi` auto-instruments all HTTP endpoints — request counts, latency histograms, and error rates are available with no custom code
- Custom business metrics are added at key domain boundaries to make system usage visible:

| Metric | Type | Purpose |
|---|---|---|
| `workman.brief.requests` | Counter | Task brief fetches by task id and status — shows what's actively being worked |
| `workman.completion.rejections` | Counter | API rejections on `status: complete` by rejection reason — shows where agents get blocked |
| `workman.notes.surfaced_per_brief` | Histogram | Notes injected per brief by tag — shows which scope tags are pulling weight |
| `workman.embeddings.refresh_triggers` | Counter | Embedding recomputes triggered by doc updates — shows design doc churn |
| `workman.issues.created` | Counter | Issue documents created, labelled by linked task — shows where work is rough |
| `workman.task.next_calls` | Counter | `workman task next` invocations — primary signal for agent activity level |
| `workman.tooldocs.reindex` | Counter | Tool doc reindex runs, labelled success/failure — confirms scheduled job health |

### Configuration

OTLP endpoint is set via `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable, consistent with other services in the stack. Metrics and traces are both enabled by default; either can be disabled independently via `OTEL_METRICS_EXPORTER=none` or `OTEL_TRACES_EXPORTER=none`.

---



All existing skill services use `BAAI/bge-small-en-v1.5` via `fastembed.TextEmbedding`. Work-manager will use the same model to ensure cross-service semantic search consistency during migration and beyond. The model name is exposed as a deployment config value (`EMBEDDING_MODEL`) so it can be changed without a code change if needed. All content is re-embedded on import.

---

## Archival & Retention

No entity is ever deleted automatically. Deletion is a manual, UI-only operation requiring explicit user action.

Archival is a first-class system feature available on all entity types (tasks, epics, notes, issues, runbooks, design docs). Archived entities:

- Are excluded from active discovery, briefs, and search results by default
- Remain queryable via an explicit `--archived` flag on CLI commands and a toggle in the UI
- Retain all their data, history, and relationships intact

This mirrors the existing notes service archive behavior and extends it consistently across the full entity model. There is no automated archival — archive actions are always intentional.

---

## Open Questions

- Should tool-docs re-indexing be on a schedule or triggered manually? (Recommendation: scheduled via APScheduler `AsyncIOScheduler` on a configurable cron interval, with a manual trigger endpoint as an override — low implementation cost, prevents stale docs)