from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, set_updated, utcnow
from ..models import Runbook
from ..schemas import RunbookCreate, RunbookUpdate
from ..serializers import runbook_dict

router = APIRouter(tags=["runbooks"])


@router.get("/runbooks")
def list_runbooks(
    db: Session = Depends(get_db),
    service: str | None = None,
    category: str | None = None,
    status: str | None = None,
):
    query = db.query(Runbook)
    if service:
        query = query.filter(Runbook.service == service)
    if category:
        query = query.filter(Runbook.category == category)
    if status:
        query = query.filter(Runbook.status == status)
    return [runbook_dict(runbook) for runbook in query.order_by(Runbook.created_at.desc()).all()]


@router.post("/runbooks")
def create_runbook(payload: RunbookCreate, db: Session = Depends(get_db)):
    runbook = Runbook(slug=generate_slug(db, "runbook"), **payload.model_dump())
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
    for key, value in payload.model_dump(exclude_unset=True).items():
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
