from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(String, nullable=True)  # comma-separated
    session_id = Column(String, nullable=True)
    supersedes = Column(String, nullable=True)
    status = Column(String, default="active")  # active | stale
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    sections = relationship("Section", back_populates="document", cascade="all, delete-orphan", order_by="Section.position")


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    slug = Column(String, nullable=False, index=True)  # doc_slug#heading_slug
    heading = Column(String, nullable=False)
    heading_slug = Column(String, nullable=False)
    level = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)
    position = Column(Integer, nullable=False)

    document = relationship("Document", back_populates="sections")
