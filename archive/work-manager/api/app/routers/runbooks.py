from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, set_updated, utcnow
from ..models import Project, Runbook
from ..schemas import RunbookCreate, RunbookUpdate
from ..serializers import runbook_dict

router = APIRouter(tags=["runbooks"])


def _resolve_project_id(db: Session, project_slug: str | None) -> int | None:
    if not project_slug:
        return None
    project = db.query(Project).filter(Project.slug == project_slug).first()
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project {project_slug} not found")
    return project.id


@router.get("/runbooks")
def list_runbooks(
    db: Session = Depends(get_db),
    service: str | None = None,
    category: str | None = None,
    status: str | None = None,
    project_slug: str | None = None,
):
    query = db.query(Runbook)
    if service:
        query = query.filter(Runbook.service == service)
    if category:
        query = query.filter(Runbook.category == category)
    if status:
        query = query.filter(Runbook.status == status)
    if project_slug:
        project = db.query(Project).filter(Project.slug == project_slug).first()
        if project:
            query = query.filter(Runbook.project_id == project.id)
    return [runbook_dict(runbook) for runbook in query.order_by(Runbook.created_at.desc()).all()]


@router.post("/runbooks")
def create_runbook(payload: RunbookCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"project_slug"})
    project_id = _resolve_project_id(db, payload.project_slug)
    runbook = Runbook(slug=generate_slug(db, "runbook"), project_id=project_id, **data)
    db.add(runbook)
    db.commit()
    db.refresh(runbook)
    return runbook_dict(runbook)


@router.get("/runbooks/{slug}")
def get_runbook(slug: str, db: Session = Depends(get_db)):
    try:
        return runbook_dict(get_by_slug(db, "runbook", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/runbooks/{slug}")
def update_runbook(slug: str, payload: RunbookUpdate, db: Session = Depends(get_db)):
    try:
        runbook = get_by_slug(db, "runbook", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    updates = payload.model_dump(exclude_unset=True, exclude={"project_slug"})
    if "project_slug" in payload.model_fields_set:
        runbook.project_id = _resolve_project_id(db, payload.project_slug)
    for key, value in updates.items():
        setattr(runbook, key, value)
    set_updated(runbook)
    db.commit()
    db.refresh(runbook)
    return runbook_dict(runbook)


@router.post("/runbooks/{slug}/validate")
def validate_runbook(slug: str, db: Session = Depends(get_db)):
    try:
        runbook = get_by_slug(db, "runbook", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    runbook.last_validated_at = utcnow()
    set_updated(runbook)
    db.commit()
    db.refresh(runbook)
    return runbook_dict(runbook)
