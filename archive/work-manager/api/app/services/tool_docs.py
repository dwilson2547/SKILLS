from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session

from ..helpers import chunk_markdown, refresh_doc_chunks, repo_cache_dir, utcnow
from ..models import ToolDoc
from ..otel import tooldocs_reindex


def _run(*args: str, cwd: Path | None = None):
    subprocess.run(args, cwd=str(cwd) if cwd else None, check=True, capture_output=True, text=True)


def _clone_repo(repo_url: str, destination: Path):
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _run("git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", repo_url, str(destination))
    _run("git", "sparse-checkout", "init", "--no-cone", cwd=destination)
    _run("git", "sparse-checkout", "set", "*.md", "**/*.md", cwd=destination)


def _markdown_sections(root: Path) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    for path in sorted(root.rglob("*.md")):
        try:
            rel = path.relative_to(root)
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        sections.extend(chunk_markdown(content, file_label=str(rel)))
    return sections


def reindex_tool_doc(tool_doc: ToolDoc, db: Session):
    checkout_dir = repo_cache_dir() / tool_doc.slug
    _clone_repo(tool_doc.repo_url, checkout_dir)
    sections = _markdown_sections(checkout_dir)
    refresh_doc_chunks(db, "tool_doc", tool_doc.id, sections)
    tool_doc.last_indexed_at = utcnow()
    tool_doc.updated_at = utcnow()
    tooldocs_reindex.add(1)
