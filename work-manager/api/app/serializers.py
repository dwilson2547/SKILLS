from .models import AcceptanceCriterion, ContextDoc, ContextDocLink, DesignDoc, DocChunk, DodItem, Epic, Issue, Note, Project, Runbook, Subtask, Task, TestingLayer, ToolDoc


def project_dict(project: Project):
    return {
        "id": project.id,
        "slug": project.slug,
        "title": project.title,
        "description": project.description,
        "status": project.status,
        "tags": project.tags or [],
        "goal": project.goal,
        "blocked_reason": project.blocked_reason,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "archived_at": project.archived_at,
    }


def epic_dict(epic: Epic):
    data = {
        "id": epic.id,
        "slug": epic.slug,
        "project_id": epic.project_id,
        "title": epic.title,
        "description": epic.description,
        "status": epic.status,
        "tags": epic.tags or [],
        "blocked_reason": epic.blocked_reason,
        "created_at": epic.created_at,
        "updated_at": epic.updated_at,
        "archived_at": epic.archived_at,
    }
    if epic.project is not None:
        data["project_slug"] = epic.project.slug
    return data


def task_dict(task: Task):
    data = {
        "id": task.id,
        "slug": task.slug,
        "epic_id": task.epic_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "tags": task.tags or [],
        "assignee": task.assignee,
        "estimated_effort": task.estimated_effort,
        "context_snapshot": task.context_snapshot,
        "blocked_reason": task.blocked_reason,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "archived_at": task.archived_at,
    }
    if task.epic is not None:
        data["epic_slug"] = task.epic.slug
        if task.epic.project is not None:
            data["project_slug"] = task.epic.project.slug
    return data


def subtask_dict(subtask: Subtask):
    return {
        "id": subtask.id,
        "slug": subtask.slug,
        "task_id": subtask.task_id,
        "title": subtask.title,
        "description": subtask.description,
        "status": subtask.status,
        "tags": subtask.tags or [],
        "blocked_reason": subtask.blocked_reason,
        "created_at": subtask.created_at,
        "updated_at": subtask.updated_at,
        "archived_at": subtask.archived_at,
    }


def acceptance_dict(item: AcceptanceCriterion):
    return {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "description": item.description,
        "verified": item.verified,
        "verified_at": item.verified_at,
        "verified_by": item.verified_by,
    }


def dod_dict(item: DodItem | None):
    if item is None:
        return {"dod_description": None, "checklist": []}
    return {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "dod_description": item.dod_description,
        "checklist": item.checklist or [],
    }


def testing_layer_dict(item: TestingLayer):
    return {
        "id": item.id,
        "entity_type": item.entity_type,
        "entity_id": item.entity_id,
        "strategy_description": item.strategy_description,
        "layer": item.layer,
        "description": item.description,
        "status": item.status,
        "notes": item.notes,
        "skip_reason": item.skip_reason,
    }


def note_dict(note: Note):
    return {
        "id": note.id,
        "slug": note.slug,
        "title": note.title,
        "body": note.body,
        "tags": note.tags or [],
        "archived_at": note.archived_at,
        "created_at": note.created_at,
        "updated_at": note.updated_at,
    }


def design_doc_dict(doc: DesignDoc):
    return {
        "id": doc.id,
        "slug": doc.slug,
        "title": doc.title,
        "content": doc.content,
        "tags": doc.tags or [],
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }


def doc_chunk_dict(chunk: DocChunk):
    return {
        "id": chunk.id,
        "doc_type": chunk.doc_type,
        "doc_id": chunk.doc_id,
        "section_heading": chunk.section_heading,
        "content": chunk.content,
    }


def tool_doc_dict(doc: ToolDoc):
    return {
        "id": doc.id,
        "slug": doc.slug,
        "title": doc.title,
        "repo_url": doc.repo_url,
        "tags": doc.tags or [],
        "last_indexed_at": doc.last_indexed_at,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
    }


def issue_dict(issue: Issue):
    return {
        "id": issue.id,
        "slug": issue.slug,
        "title": issue.title,
        "severity": issue.severity,
        "status": issue.status,
        "tags": issue.tags or [],
        "linked_task_id": issue.linked_task_id,
        "linked_runbook_ids": issue.linked_runbook_ids or [],
        "triage_steps": issue.triage_steps,
        "root_cause": issue.root_cause,
        "resolution": issue.resolution,
        "lessons_learned": issue.lessons_learned,
        "created_at": issue.created_at,
        "resolved_at": issue.resolved_at,
        "archived_at": issue.archived_at,
        "linked_task_slug": issue.task.slug if issue.task else None,
    }


def runbook_dict(runbook: Runbook):
    return {
        "id": runbook.id,
        "slug": runbook.slug,
        "title": runbook.title,
        "service": runbook.service,
        "category": runbook.category,
        "version": runbook.version,
        "status": runbook.status,
        "tags": runbook.tags or [],
        "project_id": runbook.project_id,
        "project_slug": runbook.project.slug if runbook.project else None,
        "symptoms": runbook.symptoms,
        "prerequisites": runbook.prerequisites,
        "steps": runbook.steps,
        "verification": runbook.verification,
        "escalation": runbook.escalation,
        "linked_issue_ids": runbook.linked_issue_ids or [],
        "last_validated_at": runbook.last_validated_at,
        "created_at": runbook.created_at,
        "updated_at": runbook.updated_at,
    }


def context_doc_dict(doc: ContextDoc):
    return {
        "id": doc.id,
        "slug": doc.slug,
        "title": doc.title,
        "content": doc.content,
        "tags": doc.tags or [],
        "created_at": doc.created_at,
        "updated_at": doc.updated_at,
        "links": [context_doc_link_dict(link) for link in (doc.links or [])],
    }


def context_doc_link_dict(link: ContextDocLink):
    return {
        "id": link.id,
        "context_doc_id": link.context_doc_id,
        "entity_type": link.entity_type,
        "entity_slug": link.entity_slug,
    }
