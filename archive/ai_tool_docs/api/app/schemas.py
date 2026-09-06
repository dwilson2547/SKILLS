from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


# ── Source ────────────────────────────────────────────────────────────────────

class SourceCreate(BaseModel):
    name: str
    repo: str
    branch: str = "main"
    docs_folders: list[str] = []
    file_glob: str = "*.md"

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: str) -> str:
        parts = v.strip().split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("repo must be in 'owner/repo' format")
        return v.strip()


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    repo: Optional[str] = None
    branch: Optional[str] = None
    docs_folders: Optional[list[str]] = None
    file_glob: Optional[str] = None

    @field_validator("repo")
    @classmethod
    def validate_repo(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parts = v.strip().split("/")
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("repo must be in 'owner/repo' format")
        return v.strip()


class SourceOut(BaseModel):
    id: int
    name: str
    repo: str
    branch: str
    docs_folders: list[str]
    file_glob: str
    last_commit_sha: Optional[str]
    last_synced_at: Optional[datetime]
    status: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    section_count: int = 0

    model_config = {"from_attributes": True}


# ── DocSection ────────────────────────────────────────────────────────────────

class DocSectionOut(BaseModel):
    id: int
    source_id: int
    file_path: str
    heading: Optional[str]
    level: int
    content: str
    position: int
    synced_at: datetime

    model_config = {"from_attributes": True}


class SearchResult(BaseModel):
    section: DocSectionOut
    source_name: str
    score: float


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsOut(BaseModel):
    source_count: int
    section_count: int
    file_count: int
