from datetime import datetime
from typing import Optional
import threading

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DocSection, Source
from ..schemas import SourceCreate, SourceOut, SourceUpdate
from .. import sync as sync_module

router = APIRouter(prefix="/sources", tags=["sources"])


def _source_out(source: Source, db: Session) -> SourceOut:
    count = (
        db.query(DocSection)
        .filter(DocSection.source_id == source.id)
        .count()
    )
    return SourceOut(
        **{
            col: getattr(source, col)
            for col in [
                "id", "name", "repo", "branch", "docs_folders", "file_glob",
                "last_commit_sha", "last_synced_at", "status", "error_message",
                "created_at", "updated_at",
            ]
        },
        section_count=count,
    )


# ── List ──────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    sources = db.query(Source).order_by(Source.name).all()
    return [_source_out(s, db) for s in sources]


# ── Create ────────────────────────────────────────────────────────────────────

@router.post("", response_model=SourceOut, status_code=201)
def create_source(body: SourceCreate, db: Session = Depends(get_db)):
    if db.query(Source).filter(Source.name == body.name).first():
        raise HTTPException(status_code=409, detail=f"Source '{body.name}' already exists")
    source = Source(
        name=body.name,
        repo=body.repo,
        branch=body.branch,
        docs_folders=body.docs_folders,
        file_glob=body.file_glob,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return _source_out(source, db)


# ── Get one ───────────────────────────────────────────────────────────────────

@router.get("/{source_id}", response_model=SourceOut)
def get_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return _source_out(source, db)


# ── Update ────────────────────────────────────────────────────────────────────

@router.put("/{source_id}", response_model=SourceOut)
def update_source(source_id: int, body: SourceUpdate, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if body.name is not None:
        existing = db.query(Source).filter(
            Source.name == body.name, Source.id != source_id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Source '{body.name}' already exists")
        source.name = body.name
    if body.repo is not None:
        source.repo = body.repo
        # Reset SHA so next sync re-indexes everything
        source.last_commit_sha = None
    if body.branch is not None:
        source.branch = body.branch
        source.last_commit_sha = None
    if body.docs_folders is not None:
        source.docs_folders = body.docs_folders
        source.last_commit_sha = None
    if body.file_glob is not None:
        source.file_glob = body.file_glob
        source.last_commit_sha = None

    source.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(source)
    return _source_out(source, db)


# ── Delete ────────────────────────────────────────────────────────────────────

@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()


# ── Trigger sync ──────────────────────────────────────────────────────────────

@router.post("/{source_id}/sync", status_code=202)
def trigger_sync(
    source_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status == "syncing":
        raise HTTPException(status_code=409, detail="Sync already in progress")

    background_tasks.add_task(
        lambda: threading.Thread(
            target=sync_module.sync_source, args=(source_id,), daemon=True
        ).start()
    )
    return {"detail": "Sync started", "source_id": source_id}


# ── Files list for a source ───────────────────────────────────────────────────

@router.get("/{source_id}/files")
def list_files(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    rows = (
        db.query(DocSection.file_path)
        .filter(DocSection.source_id == source_id)
        .distinct()
        .order_by(DocSection.file_path)
        .all()
    )
    return [r[0] for r in rows]
