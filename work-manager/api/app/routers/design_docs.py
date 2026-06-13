from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, refresh_design_doc_chunks, set_updated
from ..models import DocChunk, DesignDoc, Epic
from ..schemas import DesignDocCreate, DesignDocUpdate
from ..serializers import design_doc_dict, doc_chunk_dict

router = APIRouter(tags=["design_docs"])


@router.get("/design-docs")
def list_design_docs(db: Session = Depends(get_db)):
    return [design_doc_dict(doc) for doc in db.query(DesignDoc).order_by(DesignDoc.created_at.desc()).all()]


@router.post("/design-docs")
def create_design_doc(payload: DesignDocCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"epic_slug"})
    doc = DesignDoc(slug=generate_slug(db, "design_doc"), **data)
    db.add(doc)
    db.flush()
    refresh_design_doc_chunks(db, doc)
    if payload.epic_slug:
        epic = db.query(Epic).filter(Epic.slug == payload.epic_slug).first()
        if epic is None:
            raise HTTPException(status_code=404, detail=f"Epic {payload.epic_slug} not found")
        epic.design_docs.append(doc)
    db.commit()
    db.refresh(doc)
    return design_doc_dict(doc)


@router.get("/design-docs/{slug}")
def get_design_doc(slug: str, db: Session = Depends(get_db)):
    try:
        return design_doc_dict(get_by_slug(db, "design_doc", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/design-docs/{slug}")
def update_design_doc(slug: str, payload: DesignDocUpdate, db: Session = Depends(get_db)):
    try:
        doc = get_by_slug(db, "design_doc", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    updates = payload.model_dump(exclude_unset=True)
    content_changed = "content" in updates
    for key, value in updates.items():
        setattr(doc, key, value)
    set_updated(doc)
    if content_changed:
        refresh_design_doc_chunks(db, doc)
    db.commit()
    db.refresh(doc)
    return design_doc_dict(doc)


@router.get("/design-docs/{slug}/chunks")
def list_design_doc_chunks(slug: str, db: Session = Depends(get_db)):
    try:
        doc = get_by_slug(db, "design_doc", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    chunks = db.query(DocChunk).filter(DocChunk.doc_type == "design_doc", DocChunk.doc_id == doc.id).order_by(DocChunk.id.asc()).all()
    return [doc_chunk_dict(chunk) for chunk in chunks]


@router.delete("/design-docs/{slug}/chunks")
def delete_design_doc_chunks(slug: str, db: Session = Depends(get_db)):
    try:
        doc = get_by_slug(db, "design_doc", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    deleted = db.query(DocChunk).filter(DocChunk.doc_type == "design_doc", DocChunk.doc_id == doc.id).delete()
    db.commit()
    return {"deleted": deleted}
