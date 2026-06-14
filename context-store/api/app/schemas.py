from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class DocumentCreate(BaseModel):
    slug: str
    title: str = ""
    description: Optional[str] = None
    content: str
    tags: Optional[str] = None
    session_id: Optional[str] = None
    supersedes: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[str] = None
    session_id: Optional[str] = None


class StatusUpdate(BaseModel):
    status: str  # active | stale


class SectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    heading: str
    heading_slug: str
    level: int
    content: str
    position: int
    slug: str


class TocEntry(BaseModel):
    heading: str
    level: int
    slug: str
    position: int


class TocOut(BaseModel):
    slug: str
    title: str
    description: Optional[str]
    sections: list[TocEntry]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: Optional[str]
    tags: Optional[str]
    session_id: Optional[str]
    supersedes: Optional[str]
    status: str
    content: str
    created_at: datetime
    updated_at: datetime


class DocumentMeta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    description: Optional[str]
    tags: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime


class SearchRequest(BaseModel):
    query: str
    scope: Optional[str] = None
    limit: int = 5
    status: str = "active"


class SearchResult(BaseModel):
    document_slug: str
    document_title: str
    section_heading: str
    section_slug: str
    score: float
    preview: str
