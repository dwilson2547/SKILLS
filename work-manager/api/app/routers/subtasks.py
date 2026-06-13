from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, TERMINAL_STATES, get_by_slug, set_updated, utcnow
from ..models import AcceptanceCriterion, DodItem, Subtask, TestingLayer
from ..schemas import AcceptanceCriterionCreate, AcceptanceCriterionUpdate, DodUpdate, SubtaskUpdate, TestingLayerCreate, TestingLayerUpdate
from ..serializers import acceptance_dict, dod_dict, subtask_dict, testing_layer_dict
from ..services.completion import ensure_completion, invalidate_parent_completion

router = APIRouter(tags=["subtasks"])


@router.get("/subtasks/{slug}")
def get_subtask(slug: str, db: Session = Depends(get_db)):
    try:
        return subtask_dict(get_by_slug(db, "subtask", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/subtasks/{slug}")
def update_subtask(slug: str, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    previous_status = subtask.status
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(subtask, key, value)
    set_updated(subtask)
    if payload.status == "complete":
        ensure_completion("subtask", subtask.id, db)
    if previous_status in TERMINAL_STATES and subtask.status not in TERMINAL_STATES:
        invalidate_parent_completion("subtask", subtask.id, db)
    db.commit()
    db.refresh(subtask)
    return subtask_dict(subtask)


@router.post("/subtasks/{slug}/acceptance-criteria")
def create_acceptance(slug: str, payload: AcceptanceCriterionCreate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = AcceptanceCriterion(entity_type="subtask", entity_id=subtask.id, **payload.model_dump())
    if item.verified and not item.verified_at:
        item.verified_at = utcnow()
    db.add(item)
    db.commit()
    db.refresh(item)
    return acceptance_dict(item)


@router.patch("/subtasks/{slug}/acceptance-criteria/{item_id}")
def update_acceptance(slug: str, item_id: int, payload: AcceptanceCriterionUpdate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(AcceptanceCriterion).filter_by(id=item_id, entity_type="subtask", entity_id=subtask.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Acceptance criterion not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    if updates.get("verified") is True:
        item.verified_at = utcnow()
    elif updates.get("verified") is False:
        item.verified_at = None
    db.commit()
    db.refresh(item)
    return acceptance_dict(item)


@router.delete("/subtasks/{slug}/acceptance-criteria/{item_id}")
def delete_acceptance(slug: str, item_id: int, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(AcceptanceCriterion).filter_by(id=item_id, entity_type="subtask", entity_id=subtask.id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Acceptance criterion not found")
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.post("/subtasks/{slug}/testing-layers")
def create_testing_layer(slug: str, payload: TestingLayerCreate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layer = TestingLayer(entity_type="subtask", entity_id=subtask.id, **payload.model_dump())
    db.add(layer)
    db.commit()
    db.refresh(layer)
    return testing_layer_dict(layer)


@router.patch("/subtasks/{slug}/testing-layers/{item_id}")
def update_testing_layer(slug: str, item_id: int, payload: TestingLayerUpdate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layer = db.query(TestingLayer).filter_by(id=item_id, entity_type="subtask", entity_id=subtask.id).first()
    if layer is None:
        raise HTTPException(status_code=404, detail="Testing layer not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(layer, key, value)
    db.commit()
    db.refresh(layer)
    return testing_layer_dict(layer)


@router.delete("/subtasks/{slug}/testing-layers/{item_id}")
def delete_testing_layer_endpoint(slug: str, item_id: int, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    layer = db.query(TestingLayer).filter_by(id=item_id, entity_type="subtask", entity_id=subtask.id).first()
    if layer is None:
        raise HTTPException(status_code=404, detail="Testing layer not found")
    db.delete(layer)
    db.commit()
    return {"ok": True}


@router.get("/subtasks/{slug}/dod")
def get_dod(slug: str, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(DodItem).filter_by(entity_type="subtask", entity_id=subtask.id).first()
    return dod_dict(item)


@router.patch("/subtasks/{slug}/dod")
def update_dod(slug: str, payload: DodUpdate, db: Session = Depends(get_db)):
    try:
        subtask = get_by_slug(db, "subtask", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    item = db.query(DodItem).filter_by(entity_type="subtask", entity_id=subtask.id).first()
    if item is None:
        item = DodItem(entity_type="subtask", entity_id=subtask.id)
        db.add(item)
    item.dod_description = payload.dod_description
    item.checklist = payload.checklist
    db.commit()
    db.refresh(item)
    return dod_dict(item)
