---
name: project-tldr
description: 'Generate a concise TL;DR README and architecture diagrams for a project. Use when the user asks to document a project, generate a README, create architecture diagrams, or produce a project overview.'
---

# Project TL;DR

Produce a README and Mermaid diagram set that gives a competent developer a complete picture
of the project at a glance. No fluff — scope and mechanics only.

---

## Output Structure

```
README.md                  # Main overview — ≤200 lines
ARCHITECTURE.md            # All diagrams — ≤200 lines
docs/
  <subsystem>.md           # One per major subsystem — ≤200 lines each
```

Create sub-documents only when a subsystem is complex enough that its detail would push
the main README past 200 lines. Each sub-doc covers one cohesive system only.

---

## Step 1 — Analyze the Project

Before writing anything, read enough of the codebase to answer:
- What does this project do in one sentence?
- What are the active services/components and what does each own?
- How do components talk to each other (protocols, ports, message passing)?
- What are the main user-facing workflows?
- Where does data live and how does it flow?
- What are the network boundaries and ingress points?
- What are the trust boundaries and auth mechanisms?

Read `CLAUDE.md`, `docker-compose.yml`, Helm values, and key entrypoints. Do not guess.

---

## Step 2 — Write README.md

Hard limit: **200 lines**.

Structure:
```markdown
# <Project Name>

<One paragraph: what it is, what problem it solves, who uses it.>

## Components

| Component | Role | Port/Endpoint |
|---|---|---|
| ... | ... | ... |

## Architecture

```mermaid
graph TD
  ...
```

## How It Works

<2-4 sentences per major workflow. Link to ARCHITECTURE.md for detail.>

## Quick Start

<Minimum viable commands to run it locally.>

## Sub-documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — diagrams: workflows, data, network, security
- [docs/<subsystem>.md](docs/<subsystem>.md) — <one line description>
```

---

## Step 3 — Write ARCHITECTURE.md

Hard limit: **200 lines**. Use Mermaid for every diagram.

Include all of the following that are applicable to the project:

### Application Workflows
One `sequenceDiagram` or `flowchart` per major user-facing workflow.
Show the full path: user → ingress → service → downstream → response.

### Data Layer
`erDiagram` or `graph` showing schemas, relationships, and ownership.
Which service owns which data. How data moves between services.

### Network Layer
`graph TD` showing network topology: ingress controllers, service mesh,
internal DNS, external dependencies, ports.

### Security
`flowchart` showing trust boundaries, auth flows, where tokens are validated,
what is public vs private, secret management.

---

## Step 4 — Write Sub-documents (if needed)

Each sub-doc covers one subsystem. Hard limit: **200 lines**.

Structure:
```markdown
# <Subsystem Name>

<One sentence: what this subsystem does.>

## Overview
<2-3 sentences on responsibilities and boundaries.>

## Components
<Table or list of pieces within this subsystem.>

## Diagram
```mermaid
...
```

## Key Flows
<Numbered steps for the 1-2 most important workflows in this subsystem.>
```

---

## Mermaid Diagram Guidelines

- Prefer `graph TD` for architecture and topology
- Use `sequenceDiagram` for request/response flows between services
- Use `erDiagram` for data models
- Use `flowchart LR` for decision flows and pipelines
- Label all arrows with the protocol or data being passed (`--HTTP POST /api/jobs-->`)
- Keep diagrams focused — one concern per diagram, no more than ~15 nodes

---

## Rules

- 200-line hard limit per file — cut prose before cutting diagrams
- No badges, no license boilerplate, no "contributing" sections unless requested
- No redundancy between README and sub-docs — README links, sub-docs detail
- Every diagram must reflect actual running code — read the source before drawing it
- If a diagram would exceed ~15 nodes, split it into two focused diagrams
