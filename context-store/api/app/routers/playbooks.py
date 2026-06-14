from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Document, Section
from ..schemas import (
    DocumentCreate,
    DocumentMeta,
    DocumentOut,
    DocumentUpdate,
    SearchRequest,
    SearchResult,
    SectionOut,
    StatusUpdate,
    TocEntry,
    TocOut,
)
from .. import embeddings
from ..sections import parse_sections

router = APIRouter()


def _build_sections(doc: Document, content: str, db: Session) -> None:
    db.query(Section).filter(Section.document_id == doc.id).delete()

    parsed = parse_sections(doc.slug, content)
    for p in parsed:
        embed_text = f"{p['heading']}\n\n{p['content']}" if p["heading"] else p["content"]
        emb = embeddings.encode(embed_text) if embed_text.strip() else None
        sec = Section(
            document_id=doc.id,
            slug=p["slug"],
            heading=p["heading"],
            heading_slug=p["heading_slug"],
            level=p["level"],
            content=p["content"],
            embedding=emb,
            position=p["position"],
        )
        db.add(sec)


def _tag_filter(doc: Document, tag_list: list[str]) -> bool:
    if not tag_list:
        return True
    doc_tags = {t.strip().lower() for t in (doc.tags or "").split(",") if t.strip()}
    return all(t in doc_tags for t in tag_list)


# ── List all documents ────────────────────────────────────────────────────────

@router.get("/playbooks", response_model=list[DocumentMeta])
def list_playbooks(
    tags: Optional[str] = None,
    scope: Optional[str] = None,
    status: str = Query("active"),
    session_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    tag_list = [t.strip().lower() for t in tags.split(",")] if tags else []

    q = db.query(Document)
    if status != "all":
        q = q.filter(Document.status == status)
    if session_id:
        q = q.filter(Document.session_id == session_id)

    results = []
    for doc in q.order_by(Document.updated_at.desc()).all():
        if scope and not (doc.slug == scope or doc.slug.startswith(scope + "/")):
            continue
        if not _tag_filter(doc, tag_list):
            continue
        results.append(doc)

    return results


# ── Slugs list ────────────────────────────────────────────────────────────────

@router.get("/slugs", response_model=list[str])
def list_slugs(
    scope: Optional[str] = None,
    status: str = Query("all"),
    db: Session = Depends(get_db),
):
    q = db.query(Document.slug)
    if status != "all":
        q = q.filter(Document.status == status)

    slugs = [row[0] for row in q.order_by(Document.slug).all()]
    if scope:
        slugs = [s for s in slugs if s == scope or s.startswith(scope + "/")]
    return slugs


# ── Semantic search ───────────────────────────────────────────────────────────

@router.post("/playbooks/search", response_model=list[SearchResult])
def search_playbooks(body: SearchRequest, db: Session = Depends(get_db)):
    if not embeddings.is_available():
        raise HTTPException(
            status_code=503,
            detail="Semantic search unavailable — embedding model not loaded",
        )
    query_vec = embeddings.encode(body.query)
    if query_vec is None:
        raise HTTPException(status_code=503, detail="Failed to encode query")

    sec_q = (
        db.query(Section)
        .join(Document)
        .filter(Section.embedding.isnot(None))
    )
    if body.status != "all":
        sec_q = sec_q.filter(Document.status == body.status)

    scored = []
    for sec in sec_q.all():
        if body.scope and not (
            sec.document.slug == body.scope
            or sec.document.slug.startswith(body.scope + "/")
        ):
            continue
        if sec.embedding is None:
            continue
        score = embeddings.cosine_similarity(query_vec, sec.embedding)
        scored.append((sec, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    out = []
    for sec, score in scored[: body.limit]:
        out.append(
            SearchResult(
                document_slug=sec.document.slug,
                document_title=sec.document.title,
                section_heading=sec.heading,
                section_slug=sec.slug,
                score=round(score, 4),
                preview=sec.content[:200],
            )
        )
    return out


# ── Create document ───────────────────────────────────────────────────────────

@router.post("/playbooks", response_model=DocumentOut, status_code=201)
def create_playbook(body: DocumentCreate, db: Session = Depends(get_db)):
    existing = db.query(Document).filter(Document.slug == body.slug).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Slug '{body.slug}' already exists — use PUT to update")

    if body.supersedes:
        old = db.query(Document).filter(Document.slug == body.supersedes).first()
        if old:
            old.status = "stale"

    doc = Document(
        slug=body.slug,
        title=body.title or body.slug,
        description=body.description,
        tags=body.tags,
        session_id=body.session_id,
        supersedes=body.supersedes,
        status="active",
        content=body.content,
    )
    db.add(doc)
    db.flush()
    _build_sections(doc, body.content, db)
    db.commit()
    db.refresh(doc)
    return doc


# ── Routes with literal suffixes after {slug:path} — must come before plain get ──

@router.get("/playbooks/{slug:path}/toc", response_model=TocOut)
def get_toc(slug: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")
    sections = [
        TocEntry(
            heading=s.heading,
            level=s.level,
            slug=s.slug,
            position=s.position,
        )
        for s in doc.sections
    ]
    return TocOut(slug=doc.slug, title=doc.title, description=doc.description, sections=sections)


@router.get("/playbooks/{slug:path}/children", response_model=list[DocumentMeta])
def get_children(slug: str, db: Session = Depends(get_db)):
    prefix = slug + "/"
    all_docs = db.query(Document).filter(Document.slug.like(prefix + "%")).all()
    # Immediate children only: no more "/" after the prefix
    children = [d for d in all_docs if "/" not in d.slug[len(prefix) :]]
    children.sort(key=lambda d: d.slug)
    return children


@router.get("/playbooks/{slug:path}/sections/{heading_slug}", response_model=SectionOut)
def get_section(slug: str, heading_slug: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")
    sec = (
        db.query(Section)
        .filter(Section.document_id == doc.id, Section.heading_slug == heading_slug)
        .first()
    )
    if not sec:
        raise HTTPException(status_code=404, detail="Section not found")
    return sec


@router.patch("/playbooks/{slug:path}/status", response_model=DocumentMeta)
def set_status(slug: str, body: StatusUpdate, db: Session = Depends(get_db)):
    if body.status not in ("active", "stale"):
        raise HTTPException(status_code=422, detail="status must be 'active' or 'stale'")
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")
    doc.status = body.status
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


# ── Get / update / delete document ───────────────────────────────────────────

@router.get("/playbooks/{slug:path}", response_model=DocumentOut)
def get_playbook(slug: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return doc


@router.put("/playbooks/{slug:path}", response_model=DocumentOut)
def update_playbook(slug: str, body: DocumentUpdate, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")

    if body.title is not None:
        doc.title = body.title
    if body.description is not None:
        doc.description = body.description
    if body.tags is not None:
        doc.tags = body.tags
    if body.session_id is not None:
        doc.session_id = body.session_id

    if body.content is not None:
        doc.content = body.content
        _build_sections(doc, body.content, db)

    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


@router.delete("/playbooks/{slug:path}", status_code=204)
def delete_playbook(slug: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.slug == slug).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Playbook not found")
    db.delete(doc)
    db.commit()
