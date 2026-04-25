"""
SafeScan — API Router Registration
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    domains,
    scans,
    vulnerabilities,
    reports,
    api_keys,
    settings,
    verification,
    admin,
    billing,
)

api_router = APIRouter()

# Register all v1 endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(domains.router, prefix="/domains", tags=["Domains"])
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(
    vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(api_keys.router, prefix="/api-keys", tags=["API Keys"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(
    verification.router, prefix="/verification", tags=["Domain Verification"]
)
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
