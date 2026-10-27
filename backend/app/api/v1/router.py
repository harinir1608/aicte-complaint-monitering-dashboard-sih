from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.institutions import router as institutions_router
from app.api.v1.endpoints.complaints import router as complaints_router
from app.api.v1.endpoints.cases import router as cases_router
from app.api.v1.endpoints.overlaps import router as overlaps_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.audit import router as audit_router
from app.api.v1.endpoints.bureaus import bureaus_router, regions_router
from app.api.v1.endpoints.sla import router as sla_router
from app.api.v1.endpoints.conflicts import router as conflicts_router

api_router = APIRouter()

# Authentication
api_router.include_router(auth_router)

# Users
api_router.include_router(users_router)

# Institutions
api_router.include_router(institutions_router)

# Complaints
api_router.include_router(complaints_router)

# Cases
api_router.include_router(cases_router)

# Overlap detection
api_router.include_router(overlaps_router)

# Dashboard
api_router.include_router(dashboard_router)

# Reports
api_router.include_router(reports_router)

# Notifications
api_router.include_router(notifications_router)

# Audit logs
api_router.include_router(audit_router)

# Bureaus and Regions
api_router.include_router(bureaus_router)
api_router.include_router(regions_router)

# SLA rules
api_router.include_router(sla_router)

# Conflict prevention
api_router.include_router(conflicts_router)
