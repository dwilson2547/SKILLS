"""Daily background scheduler — checks all sources for updates every 24 hours."""
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .database import SessionLocal
from . import sync as sync_module

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(daemon=True)


def _daily_sync_all() -> None:
    db = SessionLocal()
    try:
        from .models import Source

        sources = db.query(Source).filter(Source.status != "syncing").all()
        source_ids = [s.id for s in sources]
    finally:
        db.close()

    logger.info("Scheduler: running daily sync for %d source(s)", len(source_ids))
    for sid in source_ids:
        try:
            sync_module.sync_source(sid)
        except Exception as exc:
            logger.error("Scheduler: sync failed for source %d: %s", sid, exc)


def start() -> None:
    _scheduler.add_job(
        _daily_sync_all,
        trigger="interval",
        hours=24,
        id="daily_sync",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler started — daily sync every 24 h")


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
