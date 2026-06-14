from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import DocSection, Source
from ..schemas import DocSectionOut, SearchResult, StatsOut
from .. import embeddings

router = APIRouter(tags=["docs"])


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsOut)
def get_stats(db: Session = Depends(get_db)):
    source_count = db.query(Source).count()
    section_count = db.query(DocSection).count()
    file_count = (
        db.query(DocSection.file_path)
        .distinct()
        .count()
    )
    return StatsOut(
        source_count=source_count,
        section_count=section_count,
        file_count=file_count,
    )


# ── Semantic search — register before /docs/{id} ─────────────────────────────

@router.get("/docs/search", response_model=list[SearchResult])
def search_docs(
    q: str = Query(..., min_length=1),
    source_id: Optional[int] = None,
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

    base_q = db.query(DocSection, Source.name).join(
        Source, DocSection.source_id == Source.id
    )
    if source_id is not None:
        base_q = base_q.filter(DocSection.source_id == source_id)

    scored = []
    for section, source_name in base_q.all():
        if section.embedding is None:
            continue
        score = embeddings.cosine_similarity(query_vec, section.embedding)
        scored.append((section, source_name, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    return [
        SearchResult(section=sec, source_name=name, score=score)
        for sec, name, score in scored[:limit]
    ]


# ── List sections ─────────────────────────────────────────────────────────────

@router.get("/docs", response_model=list[DocSectionOut])
def list_docs(
    source_id: Optional[int] = None,
    file_path: Optional[str] = None,
    sort: str = Query("default", pattern="^(default|recent)$"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(DocSection)
    if source_id is not None:
        q = q.filter(DocSection.source_id == source_id)
    if file_path is not None:
        q = q.filter(DocSection.file_path == file_path)
    if sort == "recent":
        q = q.order_by(DocSection.synced_at.desc(), DocSection.position)
    else:
        q = q.order_by(DocSection.file_path, DocSection.position)
    return q.offset(offset).limit(limit).all()


# ── Get one section ───────────────────────────────────────────────────────────

@router.get("/docs/{doc_id}", response_model=DocSectionOut)
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    section = db.get(DocSection, doc_id)
    if not section:
        raise HTTPException(status_code=404, detail="Doc section not found")
    return section
