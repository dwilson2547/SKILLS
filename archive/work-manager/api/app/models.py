from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Table, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow():
    return datetime.utcnow()


epic_design_docs = Table(
    "epic_design_docs",
    Base.metadata,
    Column("epic_id", ForeignKey("epics.id"), primary_key=True),
    Column("design_doc_id", ForeignKey("design_docs.id"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="draft")
    tags = Column(JSON, default=list)
    goal = Column(Text)
    blocked_reason = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    archived_at = Column(DateTime)

    epics = relationship("Epic", back_populates="project", cascade="all, delete-orphan")


class Epic(Base):
    __tablename__ = "epics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="draft")
    tags = Column(JSON, default=list)
    blocked_reason = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    archived_at = Column(DateTime)

    project = relationship("Project", back_populates="epics")
    tasks = relationship("Task", back_populates="epic", cascade="all, delete-orphan")
    design_docs = relationship("DesignDoc", secondary=epic_design_docs, back_populates="epics")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    epic_id = Column(Integer, ForeignKey("epics.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="draft")
    tags = Column(JSON, default=list)
    assignee = Column(String)
    estimated_effort = Column(String)
    context_snapshot = Column(Text)
    blocked_reason = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    archived_at = Column(DateTime)

    epic = relationship("Epic", back_populates="tasks")
    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")
    issues = relationship("Issue", back_populates="task")


class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="draft")
    tags = Column(JSON, default=list)
    blocked_reason = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)
    archived_at = Column(DateTime)

    task = relationship("Task", back_populates="subtasks")


class AcceptanceCriterion(Base):
    __tablename__ = "acceptance_criteria"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime)
    verified_by = Column(String)


class DodItem(Base):
    __tablename__ = "dod_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    dod_description = Column(Text)
    checklist = Column(JSON, default=list)


class TestingLayer(Base):
    __tablename__ = "testing_layers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    strategy_description = Column(Text)
    layer = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, nullable=False, default="pending")
    notes = Column(Text)
    skip_reason = Column(Text)


class ItemDependency(Base):
    __tablename__ = "item_dependencies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=False)
    depends_on_type = Column(String, nullable=False)
    depends_on_id = Column(Integer, nullable=False)


class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    embedding = Column(JSON, default=list)
    archived_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)


class DesignDoc(Base):
    __tablename__ = "design_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    epics = relationship("Epic", secondary=epic_design_docs, back_populates="design_docs")


class DocChunk(Base):
    __tablename__ = "doc_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_type = Column(String, nullable=False)
    doc_id = Column(Integer, nullable=False)
    section_heading = Column(String)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, default=list)


class ToolDoc(Base):
    __tablename__ = "tool_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    tags = Column(JSON, default=list)
    last_indexed_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)


class Issue(Base):
    __tablename__ = "issues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    tags = Column(JSON, default=list)
    linked_task_id = Column(Integer, ForeignKey("tasks.id"))
    linked_runbook_ids = Column(JSON, default=list)
    triage_steps = Column(Text)
    root_cause = Column(Text)
    resolution = Column(Text)
    lessons_learned = Column(Text)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    resolved_at = Column(DateTime)
    archived_at = Column(DateTime)

    task = relationship("Task", back_populates="issues")


class ContextDoc(Base):
    __tablename__ = "context_docs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    links = relationship("ContextDocLink", back_populates="context_doc", cascade="all, delete-orphan")


class ContextDocLink(Base):
    __tablename__ = "context_doc_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    context_doc_id = Column(Integer, ForeignKey("context_docs.id"), nullable=False)
    entity_type = Column(String, nullable=False)
    entity_slug = Column(String, nullable=False)

    context_doc = relationship("ContextDoc", back_populates="links")


class Runbook(Base):
    __tablename__ = "runbooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String, nullable=False)
    service = Column(String, nullable=False)
    category = Column(String, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    status = Column(String, nullable=False, default="draft")
    tags = Column(JSON, default=list)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    symptoms = Column(Text)
    prerequisites = Column(Text)
    steps = Column(Text)
    verification = Column(Text)
    escalation = Column(Text)
    linked_issue_ids = Column(JSON, default=list)
    last_validated_at = Column(DateTime)
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, nullable=False)

    project = relationship("Project")
