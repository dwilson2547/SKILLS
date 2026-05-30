from __future__ import annotations

from sqlalchemy.orm import Session

from ..embeddings import cosine_similarity, get_embedding
from ..helpers import TERMINAL_STATES, dependency_target
from ..models import AcceptanceCriterion, DocChunk, DodItem, Epic, Issue, ItemDependency, Note, Runbook, Subtask, Task, TestingLayer
from ..otel import brief_requests, notes_surfaced
from .completion import enforce_completion


def assemble_task_brief(slug: str, db: Session) -> dict:
    task = db.query(Task).join(Task.epic).join(Epic.project).filter(Task.slug == slug).first()
    if task is None:
        raise ValueError(f"Task {slug} not found")

    epic = task.epic
    project = epic.project
    task_tags = set((project.tags or []) + (epic.tags or []) + (task.tags or []))

    query_text = "\n".join(filter(None, [task.title, task.description or "", task.context_snapshot or "", " ".join(task_tags)]))
    query_embedding = get_embedding(query_text)

    sibling_tasks = [
        {"slug": item.slug, "title": item.title, "status": item.status}
        for item in db.query(Task).filter(Task.epic_id == epic.id).order_by(Task.created_at.asc()).all()
    ]
    subtasks = [
        {"slug": item.slug, "title": item.title, "status": item.status}
        for item in db.query(Subtask).filter(Subtask.task_id == task.id).order_by(Subtask.created_at.asc()).all()
    ]
    acceptance = db.query(AcceptanceCriterion).filter_by(entity_type="task", entity_id=task.id).all()
    dod = db.query(DodItem).filter_by(entity_type="task", entity_id=task.id).first()
    testing_layers = db.query(TestingLayer).filter_by(entity_type="task", entity_id=task.id).all()

    dependencies = []
    for dependency in db.query(ItemDependency).filter_by(entity_type="task", entity_id=task.id).all():
        target = dependency_target(db, dependency.depends_on_type, dependency.depends_on_id)
        dependencies.append(
            {
                "depends_on_type": dependency.depends_on_type,
                "depends_on_id": dependency.depends_on_id,
                "slug": getattr(target, "slug", None),
                "title": getattr(target, "title", None),
                "status": getattr(target, "status", None),
                "blocked_reason": getattr(target, "blocked_reason", None),
            }
        )

    chunk_scores = []
    design_doc_ids = [doc.id for doc in epic.design_docs]
    if design_doc_ids and query_embedding:
        for chunk in db.query(DocChunk).filter(DocChunk.doc_type == "design_doc", DocChunk.doc_id.in_(design_doc_ids)).all():
            score = cosine_similarity(query_embedding, chunk.embedding or [])
            if score > 0:
                chunk_scores.append((score, chunk))
    chunk_scores.sort(key=lambda item: item[0], reverse=True)
    design_doc_context = []
    for _, chunk in chunk_scores[:3]:
        title = next((doc.title for doc in epic.design_docs if doc.id == chunk.doc_id), None)
        design_doc_context.append({"doc_title": title, "section_heading": chunk.section_heading, "content": chunk.content})

    note_scores = []
    if task_tags and query_embedding:
        for note in db.query(Note).filter(Note.archived_at.is_(None)).all():
            note_tags = set(note.tags or [])
            # Note tags use scope: prefix (e.g. scope:domain:geospatial).
            # Task tags may or may not — normalize note tags by stripping scope: for overlap check.
            normalized_note_tags = {t.removeprefix("scope:") for t in note_tags} | note_tags
            if normalized_note_tags & task_tags:
                score = cosine_similarity(query_embedding, note.embedding or [])
                if score > 0:
                    note_scores.append((score, note))
    note_scores.sort(key=lambda item: item[0], reverse=True)
    relevant_notes = [
        {"slug": note.slug, "title": note.title, "body": note.body, "tags": note.tags or []}
        for _, note in note_scores[:5]
    ]
    notes_surfaced.record(len(relevant_notes))

    linked_issues = [
        {"slug": issue.slug, "title": issue.title, "severity": issue.severity, "status": issue.status}
        for issue in db.query(Issue).filter(Issue.linked_task_id == task.id).order_by(Issue.created_at.desc()).all()
    ]
    issue_ids = [issue.id for issue in db.query(Issue).filter(Issue.linked_task_id == task.id).all()]
    active_runbooks = []
    if issue_ids:
        for runbook in db.query(Runbook).filter(Runbook.status == "active").all():
            linked = set(runbook.linked_issue_ids or [])
            if linked.intersection(issue_ids):
                active_runbooks.append({"slug": runbook.slug, "title": runbook.title, "service": runbook.service, "category": runbook.category})

    completion_blockers = enforce_completion("task", task.id, db)
    brief_requests.add(1)
    return {
        "task": {
            "slug": task.slug,
            "title": task.title,
            "status": task.status,
            "tags": task.tags or [],
            "assignee": task.assignee,
            "estimated_effort": task.estimated_effort,
            "blocked_reason": task.blocked_reason,
            "description": task.description,
        },
        "epic": {"slug": epic.slug, "title": epic.title, "status": epic.status},
        "project": {"slug": project.slug, "title": project.title},
        "sibling_tasks": sibling_tasks,
        "subtasks": subtasks,
        "acceptance_criteria": [
            {
                "id": item.id,
                "description": item.description,
                "verified": item.verified,
                "verified_by": item.verified_by,
                "verified_at": item.verified_at,
            }
            for item in acceptance
        ],
        "dod": {"dod_description": dod.dod_description if dod else None, "checklist": dod.checklist or [] if dod else []},
        "testing_layers": [
            {
                "layer": item.layer,
                "description": item.description,
                "status": item.status,
                "notes": item.notes,
                "skip_reason": item.skip_reason,
            }
            for item in testing_layers
        ],
        "dependencies": dependencies,
        "design_doc_context": design_doc_context,
        "relevant_notes": relevant_notes,
        "linked_issues": linked_issues,
        "active_runbooks": active_runbooks,
        "completion_blockers": completion_blockers,
    }


def brief_to_markdown(brief: dict) -> str:
    def bullet_list(items, formatter):
        if not items:
            return "- None"
        return "\n".join(f"- {formatter(item)}" for item in items)

    checklist = brief.get("dod", {}).get("checklist", [])
    md = [
        f"# Task Brief: {brief['task']['slug']} — {brief['task']['title']}",
        "",
        "## Overview",
        f"- Project: {brief['project']['slug']} — {brief['project']['title']}",
        f"- Epic: {brief['epic']['slug']} — {brief['epic']['title']} ({brief['epic']['status']})",
        f"- Task Status: {brief['task']['status']}",
        f"- Assignee: {brief['task'].get('assignee') or 'Unassigned'}",
        f"- Effort: {brief['task'].get('estimated_effort') or 'Unspecified'}",
        f"- Tags: {', '.join(brief['task'].get('tags') or []) or 'None'}",
        f"- Blocked Reason: {brief['task'].get('blocked_reason') or 'None'}",
        "",
        "## Description",
        brief['task'].get('description') or 'No description provided.',
        "",
        "## Completion Blockers",
        bullet_list(brief.get('completion_blockers', []), lambda item: item),
        "",
        "## Acceptance Criteria",
        bullet_list(brief.get('acceptance_criteria', []), lambda item: f"[{ 'x' if item['verified'] else ' ' }] {item['description']}"),
        "",
        "## Definition of Done",
        brief.get('dod', {}).get('dod_description') or 'No DoD description.',
        bullet_list(checklist, lambda item: f"[{ 'x' if item.get('checked') else ' ' }] {item.get('item')}" + (f" (skip: {item.get('skip_reason')})" if item.get('skip_reason') else '')),
        "",
        "## Testing Layers",
        bullet_list(brief.get('testing_layers', []), lambda item: f"{item['layer']}: {item['description']} — {item['status']}" + (f" ({item['skip_reason']})" if item.get('skip_reason') else '')),
        "",
        "## Dependencies",
        bullet_list(brief.get('dependencies', []), lambda item: f"{item.get('slug') or item['depends_on_id']} — {item.get('title') or 'Unknown'} ({item.get('status') or 'missing'})"),
        "",
        "## Sibling Tasks",
        bullet_list(brief.get('sibling_tasks', []), lambda item: f"{item['slug']} — {item['title']} ({item['status']})"),
        "",
        "## Subtasks",
        bullet_list(brief.get('subtasks', []), lambda item: f"{item['slug']} — {item['title']} ({item['status']})"),
        "",
        "## Design Doc Context",
        bullet_list(brief.get('design_doc_context', []), lambda item: f"{item['doc_title']} / {item['section_heading']}: {item['content'][:220]}"),
        "",
        "## Relevant Notes",
        bullet_list(brief.get('relevant_notes', []), lambda item: f"{item['slug']} — {item['title']}: {item['body'][:220]}"),
        "",
        "## Linked Issues",
        bullet_list(brief.get('linked_issues', []), lambda item: f"{item['slug']} — {item['title']} ({item['severity']}, {item['status']})"),
        "",
        "## Active Runbooks",
        bullet_list(brief.get('active_runbooks', []), lambda item: f"{item['slug']} — {item['title']} [{item['service']}/{item['category']}]"),
    ]
    return "\n".join(md)
