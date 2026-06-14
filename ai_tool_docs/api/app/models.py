from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    repo = Column(String(300), nullable=False)          # owner/repo
    branch = Column(String(100), default="main")
    docs_folders = Column(JSON, default=list)           # [] means whole repo
    file_glob = Column(String(100), default="*.md")
    last_commit_sha = Column(String(40), nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="idle")         # idle | syncing | error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship(
        "DocSection", back_populates="source", cascade="all, delete-orphan"
    )


class DocSection(Base):
    __tablename__ = "doc_sections"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    file_path = Column(String(500), nullable=False, index=True)
    file_sha = Column(String(40), nullable=True)        # git blob SHA for change detection
    heading = Column(String(500), nullable=True)
    level = Column(Integer, nullable=False, default=0)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    position = Column(Integer, nullable=False, default=0)
    synced_at = Column(DateTime, default=datetime.utcnow)

    source = relationship("Source", back_populates="sections")
