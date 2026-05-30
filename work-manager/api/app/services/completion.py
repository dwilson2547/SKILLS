from fastapi import HTTPException
from sqlalchemy.orm import Session

from ..helpers import TERMINAL_STATES, acceptance_for, dod_for, get_by_slug, get_model, utcnow
from ..models import AcceptanceCriterion, DodItem, Epic, Project, Subtask, Task, TestingLayer
from ..otel import completion_rejections


PARENT_INFO = {
    "subtask": ("task", "task_id"),
    "task": ("epic", "epic_id"),
    "epic": ("project", "project_id"),
}


def _entity_name(entity_type: str) -> str:
    return entity_type.replace("_", " ")


def enforce_completion(entity_type: str, entity_id: int, db: Session) -> list[str]:
    violations: list[str] = []

    unverified = db.query(AcceptanceCriterion).filter(
        AcceptanceCriterion.entity_type == entity_type,
        AcceptanceCriterion.entity_id == entity_id,
        AcceptanceCriterion.verified.is_(False),
    ).all()
    violations.extend([f"Unverified acceptance criterion: {item.description}" for item in unverified])

    pending_testing = db.query(TestingLayer).filter(
        TestingLayer.entity_type == entity_type,
        TestingLayer.entity_id == entity_id,
        TestingLayer.status == "pending",
    ).all()
    for item in pending_testing:
        if not item.skip_reason:
            violations.append(f"Testing layer '{item.layer}' is pending without a skip reason.")

    dod = db.query(DodItem).filter(DodItem.entity_type == entity_type, DodItem.entity_id == entity_id).first()
    if dod:
        for checklist_item in dod.checklist or []:
            if not checklist_item.get("checked") and not checklist_item.get("skip_reason"):
                violations.append(f"DoD item '{checklist_item.get('item', 'Unnamed item')}' is incomplete without a skip reason.")

    if entity_type == "task":
        children = db.query(Subtask).filter(Subtask.task_id == entity_id, Subtask.archived_at.is_(None)).all()
        violations.extend([f"Subtask {child.slug} is not terminal." for child in children if child.status not in TERMINAL_STATES])
    elif entity_type == "epic":
        children = db.query(Task).filter(Task.epic_id == entity_id, Task.archived_at.is_(None)).all()
        violations.extend([f"Task {child.slug} is not terminal." for child in children if child.status not in TERMINAL_STATES])
    elif entity_type == "project":
        children = db.query(Epic).filter(Epic.project_id == entity_id, Epic.archived_at.is_(None)).all()
        violations.extend([f"Epic {child.slug} is not terminal." for child in children if child.status not in TERMINAL_STATES])

    return violations


def ensure_completion(entity_type: str, entity_id: int, db: Session):
    violations = enforce_completion(entity_type, entity_id, db)
    if violations:
        completion_rejections.add(1)
        raise HTTPException(status_code=422, detail={"violations": violations})


def invalidate_parent_completion(entity_type: str, entity_id: int, db: Session):
    if entity_type not in PARENT_INFO:
        return
    model = get_model(entity_type)
    child = db.query(model).filter(model.id == entity_id).first()
    if child is None:
        return

    parent_type, fk_attr = PARENT_INFO[entity_type]
    parent_model = get_model(parent_type)
    parent = db.query(parent_model).filter(parent_model.id == getattr(child, fk_attr)).first()
    if parent is None:
        return

    if getattr(parent, "status", None) == "complete":
        parent.status = "in_review"
        parent.blocked_reason = f"Child {child.slug} was reopened."
        if hasattr(parent, "updated_at"):
            parent.updated_at = utcnow()
        invalidate_parent_completion(parent_type, parent.id, db)
