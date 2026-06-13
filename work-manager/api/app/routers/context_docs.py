from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug, refresh_context_doc_chunks, set_updated
from ..models import ContextDoc, ContextDocLink, DocChunk
from ..schemas import ContextDocCreate, ContextDocLinkCreate, ContextDocUpdate
from ..serializers import context_doc_dict, context_doc_link_dict, doc_chunk_dict

router = APIRouter(tags=["context_docs"])

VALID_ENTITY_TYPES = {"project", "epic", "task"}


def _get_context_doc(db: Session, slug: str) -> ContextDoc:
    doc = db.query(ContextDoc).filter(ContextDoc.slug == slug).first()
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Context doc {slug} not found")
    return doc


@router.get("/context-docs")
def list_context_docs(
    db: Session = Depends(get_db),
    entity_type: str | None = None,
    entity_slug: str | None = None,
):
    if entity_type and entity_slug:
        doc_ids = [
            link.context_doc_id
            for link in db.query(ContextDocLink).filter(
                ContextDocLink.entity_type == entity_type,
                ContextDocLink.entity_slug == entity_slug,
            ).all()
        ]
        docs = db.query(ContextDoc).filter(ContextDoc.id.in_(doc_ids)).order_by(ContextDoc.created_at.desc()).all()
    else:
        docs = db.query(ContextDoc).order_by(ContextDoc.created_at.desc()).all()
    return [context_doc_dict(doc) for doc in docs]


@router.post("/context-docs")
def create_context_doc(payload: ContextDocCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"entity_type", "entity_slug"})
    doc = ContextDoc(slug=generate_slug(db, "context_doc"), **data)
    db.add(doc)
    db.flush()
    refresh_context_doc_chunks(db, doc)
    if payload.entity_type and payload.entity_slug:
        if payload.entity_type not in VALID_ENTITY_TYPES:
            raise HTTPException(status_code=422, detail=f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}")
        db.add(ContextDocLink(context_doc_id=doc.id, entity_type=payload.entity_type, entity_slug=payload.entity_slug))
    db.commit()
    db.refresh(doc)
    return context_doc_dict(doc)


@router.get("/context-docs/{slug}")
def get_context_doc(slug: str, db: Session = Depends(get_db)):
    return context_doc_dict(_get_context_doc(db, slug))


@router.patch("/context-docs/{slug}")
def update_context_doc(slug: str, payload: ContextDocUpdate, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    updates = payload.model_dump(exclude_unset=True)
    content_changed = "content" in updates
    for key, value in updates.items():
        setattr(doc, key, value)
    set_updated(doc)
    if content_changed:
        refresh_context_doc_chunks(db, doc)
    db.commit()
    db.refresh(doc)
    return context_doc_dict(doc)


@router.delete("/context-docs/{slug}")
def delete_context_doc(slug: str, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    db.query(DocChunk).filter(DocChunk.doc_type == "context_doc", DocChunk.doc_id == doc.id).delete()
    db.delete(doc)
    db.commit()
    return {"deleted": slug}


@router.get("/context-docs/{slug}/toc")
def get_context_doc_toc(slug: str, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    chunks = db.query(DocChunk).filter(
        DocChunk.doc_type == "context_doc", DocChunk.doc_id == doc.id
    ).order_by(DocChunk.id.asc()).all()
    return [{"index": i, "heading": chunk.section_heading} for i, chunk in enumerate(chunks)]


@router.get("/context-docs/{slug}/chunks")
def get_context_doc_chunks(slug: str, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    chunks = db.query(DocChunk).filter(
        DocChunk.doc_type == "context_doc", DocChunk.doc_id == doc.id
    ).order_by(DocChunk.id.asc()).all()
    return [doc_chunk_dict(chunk) for chunk in chunks]


@router.post("/context-docs/{slug}/links")
def add_context_doc_link(slug: str, payload: ContextDocLinkCreate, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    if payload.entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=422, detail=f"entity_type must be one of {sorted(VALID_ENTITY_TYPES)}")
    existing = db.query(ContextDocLink).filter_by(
        context_doc_id=doc.id, entity_type=payload.entity_type, entity_slug=payload.entity_slug
    ).first()
    if existing:
        return context_doc_link_dict(existing)
    link = ContextDocLink(context_doc_id=doc.id, entity_type=payload.entity_type, entity_slug=payload.entity_slug)
    db.add(link)
    db.commit()
    db.refresh(link)
    return context_doc_link_dict(link)


@router.delete("/context-docs/{slug}/links/{entity_type}/{entity_slug}")
def remove_context_doc_link(slug: str, entity_type: str, entity_slug: str, db: Session = Depends(get_db)):
    doc = _get_context_doc(db, slug)
    deleted = db.query(ContextDocLink).filter_by(
        context_doc_id=doc.id, entity_type=entity_type, entity_slug=entity_slug
    ).delete()
    db.commit()
    return {"deleted": deleted}
