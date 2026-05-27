---
name: subagent-review
description: 'Execute an implementation plan task-by-task using fresh subagents with spec + code quality review after each task. Use when you have a plan and want isolated, reviewed implementation.'
---

# Subagent Review

Execute a plan by dispatching a fresh subagent per task, with two-stage review after each: spec compliance first, then code quality.

## When to Use

You have a plan (written or in your head). Skip brainstorming — go straight here.

## Process

```
For each task:
  1. Dispatch implementer subagent (full task text + context)
  2. Handle status (see below)
  3. Dispatch spec reviewer — verify nothing missing, nothing extra
  4. If issues: implementer fixes → re-review
  5. Dispatch code quality reviewer — verify clean, tested, maintainable
  6. If issues: implementer fixes → re-review
  7. Mark task complete, move to next

After all tasks:
  Final review of full implementation
```

**Never start code quality review before spec compliance passes.**
**Never move to next task with open issues.**

## Model Selection

- 1–2 files, clear spec → haiku
- Multi-file, integration concerns → sonnet
- Architecture judgment, broad codebase → opus

## Implementer Prompt Template

```
You are implementing: [task name]

## Task
[Full task text — paste it, don't make subagent read the plan file]

## Context
[Where this fits, dependencies, what already exists]

## Questions First
If anything is unclear about requirements, approach, or dependencies — ask before starting.

## Your Job
1. Implement exactly what the task specifies (no more, no less)
2. Write tests (TDD if specified)
3. Verify it works
4. Commit
5. Self-review before reporting

## Self-Review Checklist
- Did I implement everything requested?
- Did I build anything not requested?
- Are names clear and accurate?
- Do tests verify real behavior?
- Did I follow existing codebase patterns?

Fix anything you find, then report.

## Report Format
**Status:** DONE | DONE_WITH_CONCERNS | NEEDS_CONTEXT | BLOCKED
- What was implemented
- Files changed
- Test results
- Self-review findings

Use DONE_WITH_CONCERNS if you have doubts about correctness.
Use NEEDS_CONTEXT if you need information not provided.
Use BLOCKED if you cannot complete the task — describe exactly what's wrong.
```

## Spec Reviewer Prompt Template

```
You are verifying spec compliance for: [task name]

## What Was Requested
[Full task requirements]

## What Implementer Reports
[Implementer's summary]

## Your Job
Read the actual code — do not trust the report.

Check for:
- Missing requirements (skipped or misunderstood)
- Extra work not in spec (over-engineering, unrequested features)
- Wrong interpretation (right idea, wrong execution)

Reference actual file:line when reporting issues.

Report:
✅ Spec compliant
❌ Issues: [specific gaps with file:line references]
```

## Code Quality Reviewer Prompt Template

```
You are reviewing code quality for: [task name]

Recent commits: [base SHA]..[head SHA]

Review the diff and relevant context for:
- Correctness (logic errors, edge cases, error handling)
- Clarity (names, structure, unnecessary complexity)
- Tests (cover real behavior, not just happy path)
- Patterns (consistent with existing codebase)
- File responsibility (each file has one clear purpose)

Report:
- Strengths
- Issues (Critical / Important / Minor)
- ✅ Approved or ❌ Needs fixes
```

## Handling Implementer Status

**DONE** → proceed to spec review

**DONE_WITH_CONCERNS** → read concerns before proceeding; address correctness concerns before review, note-only observations can wait

**NEEDS_CONTEXT** → provide the missing info, re-dispatch same subagent

**BLOCKED** → assess: wrong context (provide more + re-dispatch), too complex (break smaller or upgrade model), plan is wrong (fix the plan first)

## Rules

- Fresh subagent per task — never inherit context from previous tasks
- Provide full task text in the prompt — never tell subagent to read the plan file
- Spec compliance before code quality — always
- Re-review after every fix — never accept "fixed" without verification
- No parallel implementers — they'll conflict on shared files
