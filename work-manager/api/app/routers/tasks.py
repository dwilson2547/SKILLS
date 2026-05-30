from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, TERMINAL_STATES, generate_slug, get_by_slug, has_unresolved_dependencies, set_updated, utcnow
from ..models import AcceptanceCriterion, DodItem, Epic, ItemDependency, Project, Subtask, Task, TestingLayer
from ..otel import task_next_calls
from ..schemas import AcceptanceCriterionCreate, AcceptanceCriterionUpdate, DodUpdate, SubtaskCreate, TaskUpdate, TestingLayerCreate, TestingLayerUpdate
from ..serializers import acceptance_dict, dod_dict, subtask_dict, task_dict, testing_layer_dict
from ..services.completion import ensure_completion, invalidate_parent_completion

router = APIRouter(tags=["tasks"])


def _task_query(db: Session):
    return db.query(Task).join(Task.epic).join(Epic.project)


@router.get("/tasks")
def list_tasks(db: Session = Depends(get_db), status: str | None = None, project: str | None = None, epic: str | None = None):
    query = _task_query(db)
    if status:
        query = query.filter(Task.status == status)
    if project:
        query = query.filter(Project.slug == project)
    if epic:
        query = query.filter(Epic.slug == epic)
    return [task_dict(task) for task in query.order_by(Task.created_at.asc()).all()]


@router.get("/tasks/next")
def next_task(db: Session = Depends(get_db), project: str | None = None):
    task_next_calls.add(1)
    query = _task_query(db)
    if project:
        query = query.filter(Project.slug == project)
    in_progress = query.filter(Task.status == "in_progress").order_by(Task.created_at.asc()).first()
    if in_progress:
        return {"slug": in_progress.slug}
    candidates = query.filter(Task.status.in_(["draft", "pending"])).order_by(Task.created_at.asc()).all()
    for candidate in candidates:
        if not has_unresolved_dependencies(db, "task", candidate.id):
            return {"slug": candidate.slug}
    return {"slug": None}


@router.get("/tasks/{slug}")
def get_task(slug: str, db: Session = Depends(get_db)):
    try:
        return task_dict(get_by_slug(db, "task", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/tasks/{slug}")
def update_task(slug: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    previous_status = task.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, key, value)
    set_updated(task)
    if payload.status == "complete":
        ensure_completion("task", task.id, db)
    if previous_status in TERMINAL_STATES and task.status not in TERMINAL_STATES:
        invalidate_parent_completion("task", task.id, db)
    db.commit()
    db.refresh(task)
    return task_dict(task)


@router.get("/tasks/{slug}/subtasks")
def list_subtasks(slug: str, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [subtask_dict(subtask) for subtask in db.query(Subtask).filter(Subtask.task_id == task.id).order_by(Subtask.created_at.asc()).all()]


@router.post("/tasks/{slug}/subtasks")
def create_subtask(slug: str, payload: SubtaskCreate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    subtask = Subtask(task_id=task.id, slug=generate_slug(db, "subtask"), **payload.model_dump())
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask_dict(subtask)


@router.get("/tasks/{slug}/acceptance-criteria")
def list_acceptance(slug: str, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    items = db.query(AcceptanceCriterion).filter_by(entity_type="task", entity_id=task.id).all()
    return [acceptance_dict(i) for i in items]


@router.post("/tasks/{slug}/acceptance-criteria")
def create_acceptance(slug: str, payload: AcceptanceCriterionCreate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = AcceptanceCriterion(entity_type="task", entity_id=task.id, **payload.model_dump())
    if item.verified and not item.verified_at:
        item.verified_at = utcnow()
    db.add(item)
    db.commit()
    db.refresh(item)
    return acceptance_dict(item)


@router.patch("/tasks/{slug}/acceptance-criteria/{item_id}")
def update_acceptance(slug: str, item_id: int, payload: AcceptanceCriterionUpdate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(AcceptanceCriterion).filter_by(id=item_id, entity_type="task", entity_id=task.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Acceptance criterion not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    if updates.get("verified") is True:
        item.verified_at = utcnow()
    elif updates.get("verified") is False:
        item.verified_at = None
        item.verified_by = updates.get("verified_by")
    db.commit()
    db.refresh(item)
    return acceptance_dict(item)


@router.get("/tasks/{slug}/testing-layers")
def list_testing_layers(slug: str, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layers = db.query(TestingLayer).filter_by(entity_type="task", entity_id=task.id).all()
    return [testing_layer_dict(l) for l in layers]


@router.post("/tasks/{slug}/testing-layers")
def create_testing_layer(slug: str, payload: TestingLayerCreate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layer = TestingLayer(entity_type="task", entity_id=task.id, **payload.model_dump())
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return testing_layer_dict(layer)


@router.patch("/tasks/{slug}/testing-layers/{item_id}")
def update_testing_layer(slug: str, item_id: int, payload: TestingLayerUpdate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layer = db.query(TestingLayer).filter_by(id=item_id, entity_type="task", entity_id=task.id).first()
    if layer is None:
        raise HTTPException(status_code=404, detail="Testing layer not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(layer, key, value)
    db.commit()
    db.refresh(layer)
    return testing_layer_dict(layer)


@router.get("/tasks/{slug}/dod")
def get_dod(slug: str, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(DodItem).filter_by(entity_type="task", entity_id=task.id).first()
    return dod_dict(item)


@router.patch("/tasks/{slug}/dod")
def update_dod(slug: str, payload: DodUpdate, db: Session = Depends(get_db)):
    try:
        task = get_by_slug(db, "task", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(DodItem).filter_by(entity_type="task", entity_id=task.id).first()
    if item is None:
        item = DodItem(entity_type="task", entity_id=task.id)
        db.add(item)
    item.dod_description = payload.dod_description
    item.checklist = payload.checklist
    db.commit()
    db.refresh(item)
    return dod_dict(item)
