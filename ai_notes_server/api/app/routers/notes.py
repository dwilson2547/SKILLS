from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Note
from ..schemas import (
    ImportResult,
    NoteCreate,
    NoteImport,
    NoteOut,
    NoteUpdate,
    SearchResult,
)
from .. import embeddings

router = APIRouter()


def _note_text(note: Note) -> str:
    tags = " ".join(note.tags or [])
    return f"{note.title} {tags} {note.content}"


def _matches_tags(note: Note, tag_list: list[str]) -> bool:
    if not tag_list:
        return True
    note_tags = {t.lower() for t in (note.tags or [])}
    return any(t in note_tags for t in tag_list)


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("/notes", response_model=NoteOut, status_code=201)
def create_note(body: NoteCreate, db: Session = Depends(get_db)):
    embedding = embeddings.encode(f"{body.title} {' '.join(body.tags)} {body.content}")
    note = Note(
        title=body.title,
        tags=body.tags,
        content=body.content,
        embedding=embedding,
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


# ── Semantic search — must be registered before /{note_id} ───────────────────

@router.get("/notes/search", response_model=list[SearchResult])
def semantic_search(
    q: str = Query(..., min_length=1),
    tags: Optional[str] = None,
    archived: bool = False,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    if not embeddings.is_available():
        raise HTTPException(
            status_code=503,
            detail="Semantic search unavailable — embedding model not loaded",
        )
    query_vec = embeddings.encode(q)
    if query_vec is None:
        raise HTTPException(status_code=503, detail="Failed to encode query")

    tag_list = [t.strip().lower() for t in tags.split(",")] if tags else []

    base_q = db.query(Note)
    if archived:
        base_q = base_q.filter(Note.archived_at.isnot(None))
    else:
        base_q = base_q.filter(Note.archived_at.is_(None))

    scored = []
    for note in base_q.all():
        if not _matches_tags(note, tag_list):
            continue
        if note.embedding is None:
            continue
        score = embeddings.cosine_similarity(query_vec, note.embedding)
        scored.append((note, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [SearchResult(note=n, score=s) for n, s in scored[:limit]]


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("/notes", response_model=list[NoteOut])
def list_notes(
    q: Optional[str] = None,
    tags: Optional[str] = None,
    archived: bool = False,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    tag_list = [t.strip().lower() for t in tags.split(",")] if tags else []

    base_q = db.query(Note)
    if archived:
        base_q = base_q.filter(Note.archived_at.isnot(None))
    else:
        base_q = base_q.filter(Note.archived_at.is_(None))

    results = []
    for note in base_q.order_by(Note.updated_at.desc()).all():
        if not _matches_tags(note, tag_list):
            continue
        if q:
            haystack = f"{note.title} {' '.join(note.tags or [])} {note.content}".lower()
            if q.lower() not in haystack:
                continue
        results.append(note)

    return results[offset : offset + limit]


# ── Get one ───────────────────────────────────────────────────────────────────

@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# ── Update ────────────────────────────────────────────────────────────────────

@router.put("/notes/{note_id}", response_model=NoteOut)
def update_note(note_id: int, body: NoteUpdate, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if body.title is not None:
        note.title = body.title
    if body.tags is not None:
        note.tags = body.tags
    if body.content is not None:
        note.content = body.content

    note.updated_at = datetime.utcnow()
    note.embedding = embeddings.encode(_note_text(note))

    db.commit()
    db.refresh(note)
    return note


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()


# ── Archive toggle ────────────────────────────────────────────────────────────

@router.post("/notes/{note_id}/archive", response_model=NoteOut)
def toggle_archive(note_id: int, db: Session = Depends(get_db)):
    note = db.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.archived_at = None if note.archived_at else datetime.utcnow()
    db.commit()
    db.refresh(note)
    return note


# ── Export ────────────────────────────────────────────────────────────────────

@router.get("/export")
def export_notes(db: Session = Depends(get_db)):
    notes = db.query(Note).all()
    data = [
        {
            "title": n.title,
            "tags": n.tags or [],
            "content": n.content,
            "created_at": n.created_at.isoformat() if n.created_at else None,
            "archived_at": n.archived_at.isoformat() if n.archived_at else None,
        }
        for n in notes
    ]
    return JSONResponse(
        content=data,
        headers={"Content-Disposition": "attachment; filename=notes_export.json"},
    )


# ── Import ────────────────────────────────────────────────────────────────────

@router.post("/import", response_model=ImportResult)
def import_notes(notes: list[NoteImport], db: Session = Depends(get_db)):
    imported = 0
    for item in notes:
        text = f"{item.title} {' '.join(item.tags)} {item.content}"
        note = Note(
            title=item.title,
            tags=item.tags,
            content=item.content,
            embedding=embeddings.encode(text),
            created_at=item.created_at,
            archived_at=item.archived_at,
        )
        db.add(note)
        imported += 1
    db.commit()
    return ImportResult(imported=imported, skipped=0)
