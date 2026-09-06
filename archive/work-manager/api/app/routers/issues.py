from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, set_updated, utcnow
from ..models import Issue, Task
from ..otel import issues_created
from ..schemas import IssueCreate, IssueUpdate
from ..serializers import issue_dict

router = APIRouter(tags=["issues"])


@router.get("/issues")
def list_issues(
    db: Session = Depends(get_db),
    task: str | None = None,
    status: str | None = None,
    severity: str | None = None,
):
    query = db.query(Issue)
    if task:
        linked_task = db.query(Task).filter(Task.slug == task).first()
        if not linked_task:
            return []
        query = query.filter(Issue.linked_task_id == linked_task.id)
    if status:
        query = query.filter(Issue.status == status)
    if severity:
        query = query.filter(Issue.severity == severity)
    return [issue_dict(issue) for issue in query.order_by(Issue.created_at.desc()).all()]


@router.post("/issues")
def create_issue(payload: IssueCreate, db: Session = Depends(get_db)):
    linked_task_id = None
    if payload.task_slug:
        task = db.query(Task).filter(Task.slug == payload.task_slug).first()
        if task is None:
            raise HTTPException(status_code=404, detail=f"Task {payload.task_slug} not found")
        linked_task_id = task.id
    issue = Issue(
        slug=generate_slug(db, "issue"),
        title=payload.title,
        severity=payload.severity,
        status=payload.status,
        tags=payload.tags,
        linked_task_id=linked_task_id,
        linked_runbook_ids=payload.linked_runbook_ids,
        triage_steps=payload.triage_steps,
        root_cause=payload.root_cause,
        resolution=payload.resolution,
        lessons_learned=payload.lessons_learned,
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)
    issues_created.add(1)
    return issue_dict(issue)


@router.get("/issues/{slug}")
def get_issue(slug: str, db: Session = Depends(get_db)):
    try:
        return issue_dict(get_by_slug(db, "issue", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/issues/{slug}")
def update_issue(slug: str, payload: IssueUpdate, db: Session = Depends(get_db)):
    try:
        issue = get_by_slug(db, "issue", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    updates = payload.model_dump(exclude_unset=True)
    if "task_slug" in updates:
        task_slug = updates.pop("task_slug")
        if task_slug:
            task = db.query(Task).filter(Task.slug == task_slug).first()
            if task is None:
                raise HTTPException(status_code=404, detail=f"Task {task_slug} not found")
            issue.linked_task_id = task.id
        else:
            issue.linked_task_id = None
    for key, value in updates.items():
        setattr(issue, key, value)
    if issue.status == "resolved" and not issue.resolved_at:
        issue.resolved_at = utcnow()
    if issue.status == "open":
        issue.resolved_at = None
    set_updated(issue)
    db.commit()
    db.refresh(issue)
    return issue_dict(issue)


@router.post("/issues/{slug}/resolve")
def resolve_issue(slug: str, db: Session = Depends(get_db)):
    try:
        issue = get_by_slug(db, "issue", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    missing = [
        name for name in ["triage_steps", "root_cause", "resolution", "lessons_learned"] if not getattr(issue, name)
    ]
    if missing:
        raise HTTPException(status_code=422, detail={"missing_sections": missing})
    issue.status = "resolved"
    issue.resolved_at = utcnow()
    set_updated(issue)
    db.commit()
    db.refresh(issue)
    return issue_dict(issue)
