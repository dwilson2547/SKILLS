from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .helpers import STATUS_VALUES, ensure_tags

EstimatedEffort = Literal["xs", "s", "m", "l", "xl"]
WorkStatus = Literal["draft", "in_progress", "blocked", "in_review", "complete", "abandoned"]
TestingStatus = Literal["pending", "passed", "failed", "skipped"]
TestingType = Literal["unit", "integration", "e2e", "manual", "observability"]
IssueSeverity = Literal["sev1", "sev2", "sev3"]
IssueStatus = Literal["open", "resolved"]
RunbookStatus = Literal["draft", "active", "deprecated"]


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(Model):
    title: str
    goal: str
    description: str | None = None
    status: WorkStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class ProjectUpdate(Model):
    title: str | None = None
    goal: str | None = None
    description: str | None = None
    status: WorkStatus | None = None
    tags: list[str] | None = None
    blocked_reason: str | None = None
    archived_at: datetime | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class EpicCreate(Model):
    title: str
    description: str | None = None
    status: WorkStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class EpicUpdate(Model):
    title: str | None = None
    description: str | None = None
    status: WorkStatus | None = None
    tags: list[str] | None = None
    blocked_reason: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class TaskCreate(Model):
    title: str
    description: str | None = None
    status: WorkStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    assignee: str | None = None
    estimated_effort: EstimatedEffort | None = None
    context_snapshot: str | None = None
    blocked_reason: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class TaskUpdate(Model):
    title: str | None = None
    description: str | None = None
    status: WorkStatus | None = None
    tags: list[str] | None = None
    assignee: str | None = None
    estimated_effort: EstimatedEffort | None = None
    context_snapshot: str | None = None
    blocked_reason: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class SubtaskCreate(Model):
    title: str
    description: str | None = None
    status: WorkStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class SubtaskUpdate(Model):
    title: str | None = None
    description: str | None = None
    status: WorkStatus | None = None
    tags: list[str] | None = None
    blocked_reason: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class AcceptanceCriterionCreate(Model):
    description: str
    verified: bool = False
    verified_by: str | None = None


class AcceptanceCriterionUpdate(Model):
    description: str | None = None
    verified: bool | None = None
    verified_by: str | None = None


class DodUpdate(Model):
    dod_description: str | None = None
    checklist: list[dict] = Field(default_factory=list)


class TestingLayerCreate(Model):
    strategy_description: str | None = None
    layer: TestingType
    description: str
    status: TestingStatus = "pending"
    notes: str | None = None
    skip_reason: str | None = None


class TestingLayerUpdate(Model):
    strategy_description: str | None = None
    layer: TestingType | None = None
    description: str | None = None
    status: TestingStatus | None = None
    notes: str | None = None
    skip_reason: str | None = None


class NoteCreate(Model):
    title: str
    body: str
    tags: list[str]

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str):
        if len(value) > 2000:
            raise ValueError("Note body must be 2000 characters or fewer.")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]):
        tags = ensure_tags(value)
        if not any(tag.startswith("scope:") for tag in tags):
            raise ValueError("At least one tag must start with 'scope:'.")
        return tags


class NoteUpdate(Model):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str | None):
        if value is not None and len(value) > 2000:
            raise ValueError("Note body must be 2000 characters or fewer.")
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None):
        if value is None:
            return value
        tags = ensure_tags(value)
        if not any(tag.startswith("scope:") for tag in tags):
            raise ValueError("At least one tag must start with 'scope:'.")
        return tags


class DesignDocCreate(Model):
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    epic_slug: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class DesignDocUpdate(Model):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class LinkDesignDoc(Model):
    design_doc_id: int


class ToolDocCreate(Model):
    title: str
    repo_url: str
    tags: list[str] = Field(default_factory=list)

    _normalize_tags = field_validator("tags")(ensure_tags)


class ToolDocUpdate(Model):
    title: str | None = None
    repo_url: str | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class IssueCreate(Model):
    title: str
    severity: IssueSeverity
    status: IssueStatus = "open"
    tags: list[str] = Field(default_factory=list)
    task_slug: str | None = None
    linked_runbook_ids: list[int] = Field(default_factory=list)
    triage_steps: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    lessons_learned: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class IssueUpdate(Model):
    title: str | None = None
    severity: IssueSeverity | None = None
    status: IssueStatus | None = None
    tags: list[str] | None = None
    task_slug: str | None = None
    linked_runbook_ids: list[int] | None = None
    triage_steps: str | None = None
    root_cause: str | None = None
    resolution: str | None = None
    lessons_learned: str | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class RunbookCreate(Model):
    title: str
    service: str
    category: str
    version: int = 1
    status: RunbookStatus = "draft"
    tags: list[str] = Field(default_factory=list)
    project_slug: str | None = None
    symptoms: str | None = None
    prerequisites: str | None = None
    steps: str | None = None
    verification: str | None = None
    escalation: str | None = None
    linked_issue_ids: list[int] = Field(default_factory=list)

    _normalize_tags = field_validator("tags")(ensure_tags)


class RunbookUpdate(Model):
    title: str | None = None
    service: str | None = None
    category: str | None = None
    version: int | None = None
    status: RunbookStatus | None = None
    tags: list[str] | None = None
    project_slug: str | None = None
    symptoms: str | None = None
    prerequisites: str | None = None
    steps: str | None = None
    verification: str | None = None
    escalation: str | None = None
    linked_issue_ids: list[int] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class ContextDocCreate(Model):
    title: str
    content: str
    tags: list[str] = Field(default_factory=list)
    entity_type: str | None = None
    entity_slug: str | None = None

    _normalize_tags = field_validator("tags")(ensure_tags)


class ContextDocUpdate(Model):
    title: str | None = None
    content: str | None = None
    tags: list[str] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value):
        return ensure_tags(value)


class ContextDocLinkCreate(Model):
    entity_type: str
    entity_slug: str
