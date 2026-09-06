from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


TodoStatus = Literal["open", "in_progress", "blocked", "done"]
TodoPriority = Literal["low", "medium", "high", "urgent"]
ImportMode = Literal["merge", "replace"]


class TodoBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    tags: Optional[str] = None
    priority: TodoPriority = "medium"
    status: TodoStatus = "open"


class TodoCreate(TodoBase):
    completion_description: Optional[str] = None
    completed_at: Optional[datetime] = None


class TodoUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = None
    tags: Optional[str] = None
    priority: Optional[TodoPriority] = None
    status: Optional[TodoStatus] = None
    completion_description: Optional[str] = None
    completed_at: Optional[datetime] = None


class TodoCompleteRequest(BaseModel):
    completion_description: Optional[str] = None
    completed_at: Optional[datetime] = None


class TodoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: Optional[str]
    tags: Optional[str]
    status: str
    priority: str
    completion_description: Optional[str]
    completed_at: Optional[datetime]
    id: int
    created_at: datetime
    updated_at: datetime


class TodoImportRecord(TodoBase):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    completion_description: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TodoImportRequest(BaseModel):
    mode: ImportMode = "merge"
    todos: list[TodoImportRecord]


class TodoImportResult(BaseModel):
    mode: ImportMode
    imported: int
    created: int
    updated: int
    replaced: int


class TodoExport(BaseModel):
    schema_version: int
    exported_at: datetime
    todos: list[TodoImportRecord]
