"""Core sync logic: pull docs from GitHub and index them into DocSections."""
import fnmatch
import logging
import os
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime

from .database import SessionLocal
from .models import DocSection, Source
from . import embeddings, github_client
from .sections import parse_sections

logger = logging.getLogger(__name__)

# Per-source locks to prevent concurrent syncs of the same source
_locks: dict[int, threading.Lock] = {}
_locks_mutex = threading.Lock()


def _get_lock(source_id: int) -> threading.Lock:
    with _locks_mutex:
        if source_id not in _locks:
            _locks[source_id] = threading.Lock()
        return _locks[source_id]


def sync_source(source_id: int) -> None:
    """Sync a source, skipping if a sync is already in progress."""
    lock = _get_lock(source_id)
    if not lock.acquire(blocking=False):
        logger.info("Sync already running for source %d — skipping", source_id)
        return
    try:
        _do_sync(source_id)
    finally:
        lock.release()


def _do_sync(source_id: int) -> None:
    db = SessionLocal()
    try:
        source = db.get(Source, source_id)
        if not source:
            logger.warning("sync_source: source %d not found", source_id)
            return

        source.status = "syncing"
        source.error_message = None
        db.commit()

        try:
            owner, repo = source.repo.split("/", 1)

            # ── Wiki repos: dedicated sync path ───────────────────────────────
            if github_client.is_wiki_repo(repo):
                _do_sync_wiki(db, source, source_id, owner, repo)
                return

            # ── Resolve branch (auto-detect default on 404) ───────────────────
            branch = source.branch
            try:
                latest_sha = github_client.get_latest_commit_sha(owner, repo, branch)
            except RuntimeError as exc:
                if "404" in str(exc):
                    logger.info(
                        "Source %d: branch '%s' not found — fetching repo default branch",
                        source_id, branch,
                    )
                    info = github_client.get_repo_info(owner, repo)
                    default_branch = info.get("default_branch", "main")
                    if default_branch != branch:
                        logger.info(
                            "Source %d: updating branch from '%s' to '%s'",
                            source_id, branch, default_branch,
                        )
                        source.branch = default_branch
                        branch = default_branch
                        db.commit()
                        latest_sha = github_client.get_latest_commit_sha(
                            owner, repo, branch
                        )
                    else:
                        raise
                else:
                    raise

            # ── Check for updates ─────────────────────────────────────────────

            if latest_sha == source.last_commit_sha:
                logger.info(
                    "Source %d (%s) is up to date — skipping index", source_id, source.name
                )
                source.status = "idle"
                source.last_synced_at = datetime.utcnow()
                db.commit()
                return

            # ── Get file tree ─────────────────────────────────────────────────
            tree_items = github_client.get_repo_tree(owner, repo, latest_sha)

            wanted: dict[str, str] = {}   # file_path -> blob sha
            for item in tree_items:
                if item.get("type") != "blob":
                    continue
                path: str = item["path"]
                if not github_client.is_text_file(path):
                    continue
                if not _matches_filters(path, source.docs_folders, source.file_glob):
                    continue
                wanted[path] = item.get("sha", "")

            # ── Remove sections for deleted files ─────────────────────────────
            existing_paths: set[str] = {
                row[0]
                for row in db.query(DocSection.file_path)
                .filter(DocSection.source_id == source_id)
                .distinct()
                .all()
            }
            removed = existing_paths - set(wanted.keys())
            if removed:
                db.query(DocSection).filter(
                    DocSection.source_id == source_id,
                    DocSection.file_path.in_(removed),
                ).delete(synchronize_session=False)
                logger.info(
                    "Source %d: removed sections for %d deleted file(s)", source_id, len(removed)
                )

            # ── Index changed/new files ───────────────────────────────────────
            indexed = 0
            for file_path, blob_sha in wanted.items():
                # Check if this exact blob was already indexed
                existing = (
                    db.query(DocSection)
                    .filter(
                        DocSection.source_id == source_id,
                        DocSection.file_path == file_path,
                    )
                    .first()
                )
                if existing and existing.file_sha == blob_sha:
                    continue  # unchanged

                try:
                    raw = github_client.download_file(
                        owner, repo, file_path, branch
                    )
                    _index_file(db, source_id, file_path, blob_sha, raw)
                    indexed += 1
                except Exception as exc:
                    logger.warning(
                        "Source %d: failed to index %s — %s", source_id, file_path, exc
                    )

            source.last_commit_sha = latest_sha
            source.last_synced_at = datetime.utcnow()
            source.status = "idle"
            db.commit()
            logger.info(
                "Source %d (%s) sync complete — %d file(s) indexed",
                source_id, source.name, indexed,
            )

        except Exception as exc:
            logger.error("Source %d sync failed: %s", source_id, exc)
            source.status = "error"
            source.error_message = str(exc)
            db.commit()

    finally:
        db.close()


def _do_sync_wiki(db, source, source_id: int, owner: str, repo: str) -> None:
    """Sync a GitHub wiki source via shallow git clone."""
    clone_url = f"https://github.com/{owner}/{repo}.git"

    # ── Cheap HEAD SHA check via ls-remote ───────────────────────────────────
    token = os.environ.get("GITHUB_TOKEN", "")
    env = os.environ.copy()
    if token:
        # Embed token in URL so git uses it without interactive prompt
        clone_url = f"https://{token}@github.com/{owner}/{repo}.git"

    result = subprocess.run(
        ["git", "ls-remote", clone_url, "HEAD"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git ls-remote failed: {result.stderr.strip()}")

    latest_sha = result.stdout.split()[0] if result.stdout.strip() else None
    if not latest_sha:
        raise RuntimeError(f"Could not determine HEAD SHA for {owner}/{repo}")

    if latest_sha == source.last_commit_sha:
        logger.info("Source %d (%s) wiki is up to date — skipping", source_id, source.name)
        source.status = "idle"
        source.last_synced_at = datetime.utcnow()
        db.commit()
        return

    # ── Shallow clone ─────────────────────────────────────────────────────────
    tmpdir = tempfile.mkdtemp(prefix=f"wiki-{source_id}-")
    try:
        clone_result = subprocess.run(
            ["git", "clone", "--depth=1", "--quiet", clone_url, tmpdir],
            capture_output=True, text=True, timeout=120,
        )
        if clone_result.returncode != 0:
            raise RuntimeError(f"git clone failed: {clone_result.stderr.strip()}")

        # ── Build file map from cloned directory ──────────────────────────────
        wanted: dict[str, str] = {}  # relative_path -> absolute_path
        for root, _, files in os.walk(tmpdir):
            # Skip the .git directory
            rel_root = os.path.relpath(root, tmpdir)
            if rel_root.startswith(".git") or "/.git" in rel_root:
                continue
            for fname in files:
                abs_path = os.path.join(root, fname)
                rel_path = os.path.relpath(abs_path, tmpdir)
                if not github_client.is_text_file(rel_path):
                    continue
                if not _matches_filters(rel_path, source.docs_folders, source.file_glob):
                    continue
                wanted[rel_path] = abs_path

        # ── Remove sections for deleted files ─────────────────────────────────
        existing_paths: set[str] = {
            row[0]
            for row in db.query(DocSection.file_path)
            .filter(DocSection.source_id == source_id)
            .distinct()
            .all()
        }
        removed = existing_paths - set(wanted.keys())
        if removed:
            db.query(DocSection).filter(
                DocSection.source_id == source_id,
                DocSection.file_path.in_(removed),
            ).delete(synchronize_session=False)
            logger.info(
                "Source %d: removed sections for %d deleted wiki file(s)", source_id, len(removed)
            )

        # ── Index all files (shallow clone = always fresh snapshot) ───────────
        indexed = 0
        for rel_path, abs_path in wanted.items():
            try:
                with open(abs_path, encoding="utf-8", errors="replace") as fh:
                    raw = fh.read()
                _index_file(db, source_id, rel_path, latest_sha, raw)
                indexed += 1
            except Exception as exc:
                logger.warning(
                    "Source %d: failed to index wiki file %s — %s", source_id, rel_path, exc
                )

        source.last_commit_sha = latest_sha
        source.last_synced_at = datetime.utcnow()
        source.status = "idle"
        db.commit()
        logger.info(
            "Source %d (%s) wiki sync complete — %d file(s) indexed",
            source_id, source.name, indexed,
        )

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def _matches_filters(path: str, folders: list, glob: str) -> bool:
    """Return True if path falls within the configured folders and matches the glob."""
    if folders:
        if not any(path == f or path.startswith(f + "/") for f in folders):
            return False
    filename = path.rsplit("/", 1)[-1]
    return fnmatch.fnmatch(filename, glob)


def _index_file(
    db, source_id: int, file_path: str, file_sha: str, content: str
) -> None:
    """Replace all sections for a file with freshly parsed + embedded sections."""
    # Remove old sections for this file
    db.query(DocSection).filter(
        DocSection.source_id == source_id,
        DocSection.file_path == file_path,
    ).delete(synchronize_session=False)

    doc_slug = file_path.replace("/", "-").removesuffix(".md")
    sections = parse_sections(doc_slug, content)
    now = datetime.utcnow()

    for sec in sections:
        embed_text = (
            f"{sec['heading']}\n\n{sec['content']}" if sec["heading"] else sec["content"]
        )
        emb = embeddings.encode(embed_text.strip()) if embed_text.strip() else None

        db.add(
            DocSection(
                source_id=source_id,
                file_path=file_path,
                file_sha=file_sha,
                heading=sec["heading"],
                level=sec["level"],
                content=sec["content"],
                embedding=emb,
                position=sec["position"],
                synced_at=now,
            )
        )
