import os

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from ..models import ToolDoc
from .tool_docs import reindex_tool_doc

scheduler = AsyncIOScheduler()


async def reindex_all_tool_docs(db_factory):
    db = db_factory()
    try:
        tool_docs = db.query(ToolDoc).filter(ToolDoc.repo_url.is_not(None)).all()
        for tool_doc in tool_docs:
            try:
                reindex_tool_doc(tool_doc, db)
                db.commit()
            except Exception:
                db.rollback()
    finally:
        db.close()


def _cron_kwargs(cron: str):
    fields = cron.split()
    if len(fields) != 5:
        raise ValueError("TOOL_DOCS_REINDEX_CRON must have 5 fields")
    names = ["minute", "hour", "day", "month", "day_of_week"]
    return {name: value for name, value in zip(names, fields)}


def start_scheduler(db_factory):
    cron = os.getenv("TOOL_DOCS_REINDEX_CRON", "0 3 * * *")
    if not scheduler.get_job("tool-docs-reindex"):
        scheduler.add_job(
            reindex_all_tool_docs,
            "cron",
            id="tool-docs-reindex",
            replace_existing=True,
            args=[db_factory],
            **_cron_kwargs(cron),
        )
    if not scheduler.running:
        scheduler.start()
