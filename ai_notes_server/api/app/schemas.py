from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NoteCreate(BaseModel):
    title: str
    tags: list[str] = []
    content: str


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    tags: Optional[list[str]] = None
    content: Optional[str] = None


class NoteImport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    tags: list[str] = []
    content: str
    created_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    tags: list[str]
    content: str
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None


class SearchResult(BaseModel):
    note: NoteOut
    score: float


class ImportResult(BaseModel):
    imported: int
    skipped: int
