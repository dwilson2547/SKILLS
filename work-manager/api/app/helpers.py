from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from .embeddings import batch_embeddings, get_embedding
from .models import (
    AcceptanceCriterion,
    ContextDoc,
    ContextDocLink,
    DesignDoc,
    DocChunk,
    DodItem,
    Epic,
    Issue,
    ItemDependency,
    Note,
    Project,
    Runbook,
    Subtask,
    Task,
    TestingLayer,
    ToolDoc,
)
from .otel import embedding_refreshes

STATUS_VALUES = {"draft", "in_progress", "blocked", "in_review", "complete", "abandoned"}
TERMINAL_STATES = {"complete", "abandoned"}
ENTITY_MODELS = {
    "project": Project,
    "epic": Epic,
    "task": Task,
    "subtask": Subtask,
    "note": Note,
    "design_doc": DesignDoc,
    "context_doc": ContextDoc,
    "tool_doc": ToolDoc,
    "issue": Issue,
    "runbook": Runbook,
}
SLUG_PREFIXES = {
    "project": "PROJECT",
    "epic": "EPIC",
    "task": "TASK",
    "subtask": "SUB",
    "note": "NOTE",
    "design_doc": "DOC",
    "context_doc": "CTX",
    "tool_doc": "TOOL",
    "issue": "ISSUE",
    "runbook": "RB",
}


def utcnow() -> datetime:
    return datetime.utcnow()


class NotFoundError(Exception):
    pass


def get_model(entity_type: str):
    model = ENTITY_MODELS.get(entity_type)
    if model is None:
        raise ValueError(f"Unsupported entity type: {entity_type}")
    return model


def generate_slug(db: Session, entity_type: str) -> str:
    prefix = SLUG_PREFIXES[entity_type]
    model = get_model(entity_type)
    slugs = [value for (value,) in db.query(model.slug).filter(model.slug.like(f"{prefix}-%")).all()]
    max_num = 0
    for slug in slugs:
        try:
            max_num = max(max_num, int(slug.split("-")[-1]))
        except (ValueError, IndexError):
            continue
    return f"{prefix}-{max_num + 1:03d}"


def get_by_slug(db: Session, entity_type: str, slug: str):
    model = get_model(entity_type)
    obj = db.query(model).filter(model.slug == slug).first()
    if obj is None:
        raise NotFoundError(f"{entity_type.replace('_', ' ').title()} {slug} not found")
    return obj


def ensure_tags(value: Iterable[str] | None) -> list[str]:
    return [item for item in (value or []) if item]


def set_updated(obj):
    if hasattr(obj, "updated_at"):
        obj.updated_at = utcnow()


def chunk_markdown(content: str, *, file_label: str | None = None) -> list[tuple[str, str]]:
    text = (content or "").strip()
    if not text:
        return []
    sections: list[tuple[str, str]] = []
    current_heading = file_label or "Overview"
    current_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("## "):
            if current_lines:
                body = "\n".join(current_lines).strip()
                if body:
                    sections.append((current_heading, body))
            heading = line[3:].strip() or "Section"
            current_heading = f"{file_label} — {heading}" if file_label else heading
            current_lines = []
        else:
            current_lines.append(line)
    body = "\n".join(current_lines).strip()
    if body:
        sections.append((current_heading, body))
    if not sections:
        sections.append((file_label or "Overview", text))
    return sections


def refresh_doc_chunks(db: Session, doc_type: str, doc_id: int, sections: list[tuple[str, str]]):
    db.query(DocChunk).filter(DocChunk.doc_type == doc_type, DocChunk.doc_id == doc_id).delete()
    embeddings = batch_embeddings([content for _, content in sections]) if sections else []
    for (heading, content), embedding in zip(sections, embeddings):
        db.add(
            DocChunk(
                doc_type=doc_type,
                doc_id=doc_id,
                section_heading=heading,
                content=content,
                embedding=embedding,
            )
        )
    if sections:
        embedding_refreshes.add(1)


def refresh_design_doc_chunks(db: Session, design_doc: DesignDoc):
    refresh_doc_chunks(db, "design_doc", design_doc.id, chunk_markdown(design_doc.content))


def refresh_context_doc_chunks(db: Session, context_doc: ContextDoc):
    refresh_doc_chunks(db, "context_doc", context_doc.id, chunk_markdown(context_doc.content))


def note_embedding_payload(title: str, body: str, tags: list[str]) -> str:
    return "\n".join([title, body, " ".join(tags)]).strip()


def update_note_embedding(note: Note):
    note.embedding = get_embedding(note_embedding_payload(note.title, note.body, note.tags or []))
    embedding_refreshes.add(1)


def dependency_target(db: Session, depends_on_type: str, depends_on_id: int):
    model = get_model(depends_on_type)
    return db.query(model).filter(model.id == depends_on_id).first()


def has_unresolved_dependencies(db: Session, entity_type: str, entity_id: int) -> bool:
    dependencies = db.query(ItemDependency).filter(
        ItemDependency.entity_type == entity_type,
        ItemDependency.entity_id == entity_id,
    ).all()
    for dependency in dependencies:
        target = dependency_target(db, dependency.depends_on_type, dependency.depends_on_id)
        if target is None or getattr(target, "status", None) not in TERMINAL_STATES:
            return True
    return False


def repo_cache_dir() -> Path:
    return Path("/data") / "tool_doc_checkouts"


def acceptance_for(db: Session, entity_type: str, entity_id: int):
    return db.query(AcceptanceCriterion).filter_by(entity_type=entity_type, entity_id=entity_id).all()


def testing_for(db: Session, entity_type: str, entity_id: int):
    return db.query(TestingLayer).filter_by(entity_type=entity_type, entity_id=entity_id).all()


def dod_for(db: Session, entity_type: str, entity_id: int):
    return db.query(DodItem).filter_by(entity_type=entity_type, entity_id=entity_id).first()
