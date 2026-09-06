from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Todo
from ..schemas import (
    TodoCompleteRequest,
    TodoCreate,
    TodoExport,
    TodoImportRecord,
    TodoImportRequest,
    TodoImportResult,
    TodoOut,
    TodoUpdate,
)

router = APIRouter()

STATUS_ORDER = {"open": 0, "in_progress": 1, "blocked": 2, "done": 3}
PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


def _clean_optional_text(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _normalize_tags(tags: Optional[str]) -> Optional[str]:
    if tags is None:
        return None

    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags.split(","):
        tag = raw.strip()
        if not tag:
            continue
        key = tag.lower()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(tag)
    return ",".join(normalized) or None


def _sort_todos(todos: list[Todo]) -> list[Todo]:
    return sorted(
        todos,
        key=lambda todo: (
            STATUS_ORDER.get(todo.status, 99),
            PRIORITY_ORDER.get(todo.priority, 99),
            -todo.updated_at.timestamp(),
            -todo.id,
        ),
    )


def _matches_tags(todo: Todo, tag_filter: list[str]) -> bool:
    if not tag_filter:
        return True
    todo_tags = {tag.strip().lower() for tag in (todo.tags or "").split(",") if tag.strip()}
    return all(tag in todo_tags for tag in tag_filter)


def _matches_query(todo: Todo, query: Optional[str]) -> bool:
    if not query:
        return True
    haystack = "\n".join(
        part for part in (todo.title, todo.description or "", todo.tags or "") if part
    ).lower()
    return query.lower() in haystack


def _apply_create_fields(todo: Todo, body: TodoCreate) -> None:
    todo.title = body.title.strip()
    todo.description = _clean_optional_text(body.description)
    todo.tags = _normalize_tags(body.tags)
    todo.priority = body.priority
    todo.status = body.status

    if body.status == "done":
        todo.completed_at = body.completed_at or datetime.utcnow()
        todo.completion_description = _clean_optional_text(body.completion_description)
    else:
        todo.completed_at = None
        todo.completion_description = None


def _apply_update_fields(todo: Todo, body: TodoUpdate) -> None:
    if body.title is not None:
        todo.title = body.title.strip()
    if body.description is not None:
        todo.description = _clean_optional_text(body.description)
    if body.tags is not None:
        todo.tags = _normalize_tags(body.tags)
    if body.priority is not None:
        todo.priority = body.priority

    new_status = body.status if body.status is not None else todo.status
    was_done = todo.status == "done"

    if body.status is not None:
        todo.status = body.status

    if new_status == "done":
        if body.completed_at is not None:
            todo.completed_at = body.completed_at
        elif not was_done or todo.completed_at is None:
            todo.completed_at = datetime.utcnow()

        if body.completion_description is not None:
            todo.completion_description = _clean_optional_text(body.completion_description)
    elif body.status is not None:
        todo.completed_at = None
        todo.completion_description = None

    todo.updated_at = datetime.utcnow()


def _apply_import_record(todo: Todo, item: TodoImportRecord) -> None:
    todo.title = item.title.strip()
    todo.description = _clean_optional_text(item.description)
    todo.tags = _normalize_tags(item.tags)
    todo.priority = item.priority
    todo.status = item.status
    todo.created_at = item.created_at or todo.created_at or datetime.utcnow()
    todo.updated_at = item.updated_at or datetime.utcnow()

    if item.status == "done":
        todo.completed_at = item.completed_at or datetime.utcnow()
        todo.completion_description = _clean_optional_text(item.completion_description)
    else:
        todo.completed_at = None
        todo.completion_description = None


def _get_todo_or_404(todo_id: int, db: Session) -> Todo:
    todo = db.query(Todo).filter(Todo.id == todo_id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


@router.get("/todos/export", response_model=TodoExport)
def export_todos(db: Session = Depends(get_db)):
    todos = _sort_todos(db.query(Todo).all())
    exported = [
        TodoImportRecord.model_validate(todo, from_attributes=True)
        for todo in todos
    ]
    return TodoExport(schema_version=1, exported_at=datetime.utcnow(), todos=exported)


@router.post("/todos/import", response_model=TodoImportResult)
def import_todos(body: TodoImportRequest, db: Session = Depends(get_db)):
    created = 0
    updated = 0
    replaced = 0

    if body.mode == "replace":
        replaced = db.query(Todo).count()
        db.query(Todo).delete()
        db.flush()

    for item in body.todos:
        todo = None
        if item.id is not None:
            todo = db.query(Todo).filter(Todo.id == item.id).first()

        if todo is None:
            todo = Todo()
            if item.id is not None:
                todo.id = item.id
            db.add(todo)
            created += 1
        else:
            updated += 1

        _apply_import_record(todo, item)

    db.commit()
    return TodoImportResult(
        mode=body.mode,
        imported=len(body.todos),
        created=created,
        updated=updated,
        replaced=replaced,
    )


@router.get("/todos", response_model=list[TodoOut])
def list_todos(
    status: str = Query("all"),
    priority: str = Query("all"),
    tags: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    tag_filter = [tag.strip().lower() for tag in tags.split(",") if tag.strip()] if tags else []

    query = db.query(Todo)
    if status != "all":
        query = query.filter(Todo.status == status)
    if priority != "all":
        query = query.filter(Todo.priority == priority)

    todos = [
        todo
        for todo in query.all()
        if _matches_tags(todo, tag_filter) and _matches_query(todo, q)
    ]
    return _sort_todos(todos)


@router.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(body: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo()
    _apply_create_fields(todo, body)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    return _get_todo_or_404(todo_id, db)


@router.put("/todos/{todo_id}", response_model=TodoOut)
def update_todo(todo_id: int, body: TodoUpdate, db: Session = Depends(get_db)):
    todo = _get_todo_or_404(todo_id, db)
    _apply_update_fields(todo, body)
    db.commit()
    db.refresh(todo)
    return todo


@router.patch("/todos/{todo_id}/complete", response_model=TodoOut)
def complete_todo(todo_id: int, body: TodoCompleteRequest, db: Session = Depends(get_db)):
    todo = _get_todo_or_404(todo_id, db)
    todo.status = "done"
    todo.completed_at = body.completed_at or datetime.utcnow()
    todo.completion_description = _clean_optional_text(body.completion_description)
    todo.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    todo = _get_todo_or_404(todo_id, db)
    db.delete(todo)
    db.commit()
