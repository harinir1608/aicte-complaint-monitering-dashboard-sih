from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Router imports (added progressively in Phases 2-6) ───────────────────────
# from app.api.v1 import auth, institutions, complaints, cases, overlaps,
#                        dashboard, reports, notifications, users, bureaus,
#                        regions, sla, audit


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle."""
    logger.info(
        "Starting AICTE Complaint Dashboard backend "
        "(environment: %s)",
        settings.ENVIRONMENT,
    )

    # Initialize APScheduler for deadline monitoring
    # Scheduler is configured in app.tasks.scheduler and started here
    try:
        from app.tasks.scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        logger.info("Background scheduler started.")
    except ImportError:
        logger.warning(
            "Background scheduler module not yet available — skipping."
        )

    yield

    # Graceful shutdown
    try:
        from app.tasks.scheduler import stop_scheduler  # noqa: F811
        stop_scheduler()
        logger.info("Background scheduler stopped.")
    except (ImportError, Exception):
        pass

    logger.info("AICTE Complaint Dashboard backend stopped.")


# ── Application ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AICTE Complaint Dashboard API",
    version="1.0.0",
    description=(
        "AICTE Integrated Institution Complaint Monitoring and Status Dashboard. "
        "Centralises complaint and case management across AICTE Bureaus/Cells with "
        "overlap detection, SLA monitoring, and coordinated case review."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.v1.router import api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")

# ── Health check ──────────────────────────────────────────────────────────────

@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    """Liveness probe — returns 200 when the process is running."""
    return {"status": "ok", "environment": settings.ENVIRONMENT}


@app.get("/api/v1/health", tags=["system"])
def api_health_check() -> dict[str, str]:
    """API-prefixed liveness probe for proxy health checks."""
    return {"status": "ok", "version": "1.0.0"}
