from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, set_updated
from ..models import DesignDoc, Epic, Project, Task
from ..schemas import LinkDesignDoc, EpicUpdate, TaskCreate
from ..serializers import design_doc_dict, epic_dict, task_dict
from ..services.completion import ensure_completion, invalidate_parent_completion

router = APIRouter(tags=["epics"])


@router.get("/epics")
def list_epics(db: Session = Depends(get_db), project: str | None = None, status: str | None = None):
    query = db.query(Epic)
    if project:
        parent = db.query(Project).filter(Project.slug == project).first()
        if parent:
            query = query.filter(Epic.project_id == parent.id)
        else:
            return []
    if status:
        query = query.filter(Epic.status == status)
    return [epic_dict(epic) for epic in query.order_by(Epic.created_at.asc()).all()]


@router.get("/epics/{slug}")
def get_epic(slug: str, db: Session = Depends(get_db)):
    try:
        return epic_dict(get_by_slug(db, "epic", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/epics/{slug}")
def update_epic(slug: str, payload: EpicUpdate, db: Session = Depends(get_db)):
    try:
        epic = get_by_slug(db, "epic", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    previous_status = epic.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(epic, key, value)
    set_updated(epic)
    if payload.status == "complete":
        ensure_completion("epic", epic.id, db)
    if previous_status in {"complete", "abandoned"} and epic.status not in {"complete", "abandoned"}:
        invalidate_parent_completion("epic", epic.id, db)
    db.commit()
    db.refresh(epic)
    return epic_dict(epic)


@router.get("/epics/{slug}/tasks")
def list_epic_tasks(slug: str, db: Session = Depends(get_db)):
    try:
        epic = get_by_slug(db, "epic", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [task_dict(task) for task in db.query(Task).filter(Task.epic_id == epic.id).order_by(Task.created_at.asc()).all()]


@router.post("/epics/{slug}/tasks")
def create_epic_task(slug: str, payload: TaskCreate, db: Session = Depends(get_db)):
    try:
        epic = get_by_slug(db, "epic", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    task = Task(epic_id=epic.id, slug=generate_slug(db, "task"), **payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_dict(task)


@router.get("/epics/{slug}/design-docs")
def list_epic_design_docs(slug: str, db: Session = Depends(get_db)):
    try:
        epic = get_by_slug(db, "epic", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [design_doc_dict(doc) for doc in epic.design_docs]


@router.post("/epics/{slug}/design-docs")
def link_design_doc(slug: str, payload: LinkDesignDoc, db: Session = Depends(get_db)):
    try:
        epic = get_by_slug(db, "epic", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    design_doc = db.query(DesignDoc).filter(DesignDoc.id == payload.design_doc_id).first()
    if design_doc is None:
        raise HTTPException(status_code=404, detail=f"Design doc {payload.design_doc_id} not found")
    if design_doc not in epic.design_docs:
        epic.design_docs.append(design_doc)
        set_updated(epic)
        db.commit()
    return [design_doc_dict(doc) for doc in epic.design_docs]
