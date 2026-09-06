from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, ensure_tags, generate_slug, get_by_slug, set_updated
from ..models import Project
from ..schemas import EpicCreate, ProjectCreate, ProjectUpdate
from ..serializers import epic_dict, project_dict
from ..services.completion import ensure_completion, invalidate_parent_completion
from ..models import Epic

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects(db: Session = Depends(get_db), status: str | None = None):
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    return [project_dict(project) for project in query.order_by(Project.created_at.asc()).all()]


@router.post("/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(slug=generate_slug(db, "project"), **payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project_dict(project)


@router.get("/projects/{slug}")
def get_project(slug: str, db: Session = Depends(get_db)):
    try:
        return project_dict(get_by_slug(db, "project", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/projects/{slug}")
def update_project(slug: str, payload: ProjectUpdate, db: Session = Depends(get_db)):
    try:
        project = get_by_slug(db, "project", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    previous_status = project.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, key, value)
    set_updated(project)
    if payload.status == "complete":
        ensure_completion("project", project.id, db)
    if previous_status in {"complete", "abandoned"} and project.status not in {"complete", "abandoned"}:
        project.blocked_reason = project.blocked_reason or f"Project {project.slug} was reopened."
    db.commit()
    db.refresh(project)
    return project_dict(project)


@router.get("/projects/{slug}/epics")
def list_project_epics(slug: str, db: Session = Depends(get_db)):
    try:
        project = get_by_slug(db, "project", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [epic_dict(epic) for epic in db.query(Epic).filter(Epic.project_id == project.id).order_by(Epic.created_at.asc()).all()]


@router.post("/projects/{slug}/epics")
def create_project_epic(slug: str, payload: EpicCreate, db: Session = Depends(get_db)):
    try:
        project = get_by_slug(db, "project", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    epic = Epic(project_id=project.id, slug=generate_slug(db, "epic"), **payload.model_dump())
    db.add(epic)
    db.commit()
    db.refresh(epic)
    return epic_dict(epic)
