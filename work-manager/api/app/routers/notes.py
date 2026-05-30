from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..embeddings import cosine_similarity, get_embedding
from ..helpers import NotFoundError, generate_slug, get_by_slug, set_updated, update_note_embedding, utcnow
from ..models import Note
from ..schemas import NoteCreate, NoteUpdate
from ..serializers import note_dict

router = APIRouter(tags=["notes"])


@router.get("/notes")
def list_notes(
    db: Session = Depends(get_db),
    tag: str | None = None,
    q: str | None = None,
    include_archived: bool = False,
):
    query = db.query(Note)
    if not include_archived:
        query = query.filter(Note.archived_at.is_(None))
    notes = query.order_by(Note.created_at.desc()).all()
    if tag:
        notes = [note for note in notes if tag in (note.tags or [])]
    if q:
        query_embedding = get_embedding(q)
        scored = []
        for note in notes:
            score = cosine_similarity(query_embedding, note.embedding or [])
            if score > 0:
                item = note_dict(note)
                item["score"] = score
                scored.append(item)
        return sorted(scored, key=lambda item: item["score"], reverse=True)
    return [note_dict(note) for note in notes]


@router.post("/notes")
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    note = Note(slug=generate_slug(db, "note"), **payload.model_dump())
    update_note_embedding(note)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_dict(note)


@router.get("/notes/{slug}")
def get_note(slug: str, db: Session = Depends(get_db)):
    try:
        return note_dict(get_by_slug(db, "note", slug))
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/notes/{slug}")
def update_note(slug: str, payload: NoteUpdate, db: Session = Depends(get_db)):
    try:
        note = get_by_slug(db, "note", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(note, key, value)
    update_note_embedding(note)
    set_updated(note)
    db.commit()
    db.refresh(note)
    return note_dict(note)


@router.post("/notes/{slug}/archive")
def archive_note(slug: str, db: Session = Depends(get_db)):
    try:
        note = get_by_slug(db, "note", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    note.archived_at = utcnow()
    set_updated(note)
    db.commit()
    db.refresh(note)
    return note_dict(note)


@router.post("/notes/{slug}/unarchive")
def unarchive_note(slug: str, db: Session = Depends(get_db)):
    try:
        note = get_by_slug(db, "note", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    note.archived_at = None
    set_updated(note)
    db.commit()
    db.refresh(note)
    return note_dict(note)
