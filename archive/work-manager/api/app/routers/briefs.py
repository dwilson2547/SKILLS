from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..services.brief_assembler import assemble_task_brief, brief_to_markdown

router = APIRouter(tags=["briefs"])


@router.get("/briefs/task/{slug}")
def get_task_brief(slug: str, db: Session = Depends(get_db)):
    try:
        return assemble_task_brief(slug, db)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/briefs/task/{slug}/markdown", response_class=PlainTextResponse)
def get_task_brief_markdown(slug: str, db: Session = Depends(get_db)):
    try:
        return brief_to_markdown(assemble_task_brief(slug, db))
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
