from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..helpers import NotFoundError, generate_slug, get_by_slug
from ..models import ToolDoc
from ..schemas import ToolDocCreate
from ..serializers import tool_doc_dict
from ..services.tool_docs import reindex_tool_doc

router = APIRouter(tags=["tool_docs"])


@router.get("/tool-docs")
def list_tool_docs(db: Session = Depends(get_db)):
    return [tool_doc_dict(doc) for doc in db.query(ToolDoc).order_by(ToolDoc.created_at.desc()).all()]


@router.post("/tool-docs")
def create_tool_doc(payload: ToolDocCreate, db: Session = Depends(get_db)):
    doc = ToolDoc(slug=generate_slug(db, "tool_doc"), **payload.model_dump())
    db.add(doc)
    db.flush()
    reindex_error = None
    try:
        reindex_tool_doc(doc, db)
    except Exception as exc:
        reindex_error = str(exc)
    db.commit()
    db.refresh(doc)
    data = tool_doc_dict(doc)
    if reindex_error:
        data["reindex_error"] = reindex_error
    return data


@router.post("/tool-docs/{slug}/reindex")
def reindex_tool(slug: str, db: Session = Depends(get_db)):
    try:
        doc = get_by_slug(db, "tool_doc", slug)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    try:
        reindex_tool_doc(doc, db)
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=f"Tool doc reindex failed: {exc}") from exc
    db.refresh(doc)
    return tool_doc_dict(doc)
