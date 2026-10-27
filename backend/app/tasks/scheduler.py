"""
APScheduler background scheduler.

Started during FastAPI lifespan startup and stopped on shutdown.
Jobs are idempotent: each checks whether a notification was already
sent in the last 24 hours before creating a new one.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler(daemon=True)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def check_deadlines_job() -> None:
    """Scan active cases for approaching or overdue deadlines."""
    from app.core.database import SessionLocal
    from app.services.sla_service import SLAService

    db = SessionLocal()
    try:
        svc = SLAService()
        count = svc.check_deadlines_and_notify(db)
        logger.info("check_deadlines_job: %d notification(s) created.", count)
    except Exception as exc:
        logger.error("check_deadlines_job failed: %s", exc, exc_info=True)
    finally:
        db.close()


def run_conflict_detection_job() -> None:
    """Daily job: run cross-bureau conflict detection across all active institutions."""
    from app.core.database import SessionLocal
    from app.services.conflict_service import run_global_conflict_scan

    db = SessionLocal()
    try:
        count = run_global_conflict_scan(db)
        logger.info("run_conflict_detection_job: %d new conflict alert(s) created.", count)
    except Exception as exc:
        logger.error("run_conflict_detection_job failed: %s", exc, exc_info=True)
    finally:
        db.close()


def run_overlap_detection_job() -> None:
    """Optional daily job: run overlap detection on recently updated cases."""
    from app.core.database import SessionLocal
    from app.models.case import Case, CaseStatus
    from app.matching.overlap_engine import OverlapEngine
    from datetime import datetime, timedelta, timezone

    db = SessionLocal()
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_cases = (
            db.query(Case)
            .filter(
                Case.updated_at >= cutoff,
                Case.status.notin_([CaseStatus.disposed, CaseStatus.closed]),
            )
            .all()
        )
        engine = OverlapEngine(db=db)
        total_alerts = 0
        for case in recent_cases:
            alerts = engine.run_overlap_check(case.id, db)
            total_alerts += len(alerts)
        logger.info(
            "run_overlap_detection_job: processed %d cases, created %d alerts.",
            len(recent_cases),
            total_alerts,
        )
    except Exception as exc:
        logger.error("run_overlap_detection_job failed: %s", exc, exc_info=True)
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Start / stop
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """Register jobs and start the scheduler. Safe to call multiple times."""
    if scheduler.running:
        return

    # Check deadlines every 6 hours
    scheduler.add_job(
        check_deadlines_job,
        trigger="interval",
        hours=6,
        id="check_deadlines",
        replace_existing=True,
        misfire_grace_time=300,
    )

    # Overlap detection daily at 02:00 server time
    scheduler.add_job(
        run_overlap_detection_job,
        trigger="cron",
        hour=2,
        minute=0,
        id="overlap_detection",
        replace_existing=True,
        misfire_grace_time=600,
    )

    # Conflict detection daily at 03:00 server time
    scheduler.add_job(
        run_conflict_detection_job,
        trigger="cron",
        hour=3,
        minute=0,
        id="conflict_detection",
        replace_existing=True,
        misfire_grace_time=600,
    )

    scheduler.start()
    logger.info("Background scheduler started with %d job(s).", len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Background scheduler stopped.")
