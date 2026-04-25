"""
SafeScan — Scans Endpoints
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

logger = logging.getLogger(__name__)

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.api_key_auth import get_current_user_by_api_key
from app.models.scan import Scan
from app.models.domain import Domain
from app.models.user import User
from app.models.vulnerability import Vulnerability
from app.schemas.scan import (
    ScanCreate,
    ScanResponse,
    ScanStatus,
    ScanFilters,
    ScanSummary,
)
from app.services.audit import log_audit_event
from app.workers.tasks import run_scan
from app.workers.scan_logger import ScanLogger

router = APIRouter()

# Module lists for scan types
FULL_MODULES = [
    "security_headers",
    "ssl_tls",
    "xss",
    "injection",
    "csrf_cors",
    "ssrf_xxe_traversal",
    "auth_sessions",
    "server_config",
    "sca",
    "info_leakage",
    "app_logic",
    "network",
]
QUICK_MODULES = [
    "security_headers",
    "ssl_tls",
    "server_config",
    "info_leakage",
]

# Pricing
FULL_SCAN_PRICE = 20.0  # RUB
QUICK_SCAN_PRICE = 10.0  # RUB after free scans exhausted
FREE_QUICK_SCANS = 5  # Free quick scans per user


async def get_authenticated_user(
    jwt_user: dict = Depends(get_current_user),
    api_key_user: dict = Depends(get_current_user_by_api_key),
):
    """Accept either JWT or API key authentication."""
    user = api_key_user or jwt_user
    if not user or not user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required (JWT token or X-API-Key header)",
        )
    return user


@router.post("/", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def create_scan(
    scan_data: ScanCreate,
    current_user: dict = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """Create and start a new vulnerability scan."""
    user_role = current_user.get("role", "viewer")
    is_admin = user_role in ("admin", "security_auditor")

    # Verify domain ownership and verification
    domain_result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(scan_data.domain_id),
            Domain.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    domain = domain_result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    # Non-admin users must have verified domain
    if not is_admin and not domain.is_verified:
        raise HTTPException(
            status_code=403,
            detail="Domain not verified. Please verify the domain before running a scan.",
        )

    # Determine modules and calculate cost
    if scan_data.scan_type == "full":
        modules = FULL_MODULES
        scan_cost = FULL_SCAN_PRICE
    elif scan_data.scan_type == "quick":
        modules = QUICK_MODULES
        scan_cost = QUICK_SCAN_PRICE
    else:
        modules = scan_data.modules or FULL_MODULES
        scan_cost = FULL_SCAN_PRICE

    # Handle billing (skip for admins)
    actual_cost = 0.0
    free_remaining = 0

    if not is_admin:
        user_result = await db.execute(
            select(User)
            .where(User.id == uuid.UUID(current_user["sub"]))
            .with_for_update()
        )
        user = user_result.scalar_one_or_none()

        if user:
            free_remaining = user.free_scans_remaining

            if scan_data.scan_type == "quick" and user.free_scans_remaining > 0:
                # Use free scan allowance
                user.free_scans_remaining -= 1
                free_remaining = user.free_scans_remaining
                actual_cost = 0.0
                await log_audit_event(
                    db=db,
                    user_id=uuid.UUID(current_user["sub"]),
                    action="FREE_SCAN_USED",
                    resource_type="scan",
                    resource_id=None,
                    details={
                        "remaining_free_scans": free_remaining,
                        "scan_type": scan_data.scan_type,
                    },
                )
            elif scan_cost > 0:
                # Deduct from balance
                if user.balance < scan_cost:
                    raise HTTPException(
                        status_code=402,
                        detail=f"Недостаточно средств. Стоимость скана: {scan_cost} RUB, баланс: {user.balance:.2f} RUB",
                    )
                user.balance -= scan_cost
                actual_cost = scan_cost
                await log_audit_event(
                    db=db,
                    user_id=uuid.UUID(current_user["sub"]),
                    action="SCAN_PAYMENT",
                    resource_type="scan",
                    resource_id=None,
                    details={
                        "amount": scan_cost,
                        "scan_type": scan_data.scan_type,
                        "balance_after": user.balance,
                    },
                )

    # Create scan record
    new_scan = Scan(
        domain_id=uuid.UUID(scan_data.domain_id),
        user_id=uuid.UUID(current_user["sub"]),
        scan_type=scan_data.scan_type,
        modules_enabled=modules,
        status="queued",
        consent_acknowledged=scan_data.consent_acknowledged,
        consent_timestamp=datetime.now(timezone.utc),
    )
    db.add(new_scan)
    await db.flush()

    # Send to Celery queue
    task = run_scan.delay(
        scan_id=str(new_scan.id),
        domain=domain.domain,
        modules=modules,
    )

    # Store Celery task ID for cancellation
    new_scan.celery_task_id = task.id
    new_scan.status = "running"
    new_scan.started_at = datetime.now(timezone.utc)

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="SCAN_CREATED",
        resource_type="scan",
        resource_id=new_scan.id,
        details={
            "domain": domain.domain,
            "scan_type": scan_data.scan_type,
            "modules": modules,
            "celery_task_id": task.id,
        },
    )

    await db.commit()
    await db.refresh(new_scan)

    # Build response
    return ScanResponse(
        id=str(new_scan.id),
        domain_id=str(new_scan.domain_id),
        domain=domain.domain,
        user_id=str(new_scan.user_id),
        scan_type=new_scan.scan_type,
        status=new_scan.status,
        modules_enabled=new_scan.modules_enabled,
        current_module=new_scan.current_module,
        progress_percentage=new_scan.progress_percentage,
        pages_crawled=new_scan.pages_crawled,
        requests_made=new_scan.requests_made,
        total_findings=new_scan.total_findings,
        critical_count=new_scan.critical_count,
        high_count=new_scan.high_count,
        medium_count=new_scan.medium_count,
        low_count=new_scan.low_count,
        info_count=new_scan.info_count,
        risk_score=new_scan.risk_score,
        grade=new_scan.grade,
        started_at=new_scan.started_at,
        completed_at=new_scan.completed_at,
        error_message=new_scan.error_message,
        created_at=new_scan.created_at,
        cost=actual_cost,
        free_scans_remaining=free_remaining,
    )


@router.get("/")
async def list_scans(
    status_filter: Optional[str] = Query(None, alias="status"),
    scan_type: Optional[str] = Query(None),
    current_user: dict = Depends(get_authenticated_user),
    db: AsyncSession = Depends(get_db),
):
    """List scans for current user."""
    base_query = (
        select(Scan, Domain.domain)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(Scan.user_id == uuid.UUID(current_user["sub"]))
    )

    if status_filter:
        base_query = base_query.where(Scan.status == status_filter)
    if scan_type:
        base_query = base_query.where(Scan.scan_type == scan_type)

    result = await db.execute(base_query.order_by(Scan.created_at.desc()))
    scans = result.all()

    return [
        ScanSummary(
            id=str(scan.id),
            domain=domain,
            scan_type=scan.scan_type,
            status=scan.status,
            total_findings=scan.total_findings,
            critical_count=scan.critical_count,
            high_count=scan.high_count,
            medium_count=scan.medium_count,
            low_count=scan.low_count,
            info_count=scan.info_count,
            grade=scan.grade,
            completed_at=scan.completed_at,
        )
        for scan, domain in scans
    ]


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scan details."""
    result = await db.execute(
        select(Scan, Domain.domain)
        .join(Domain, Scan.domain_id == Domain.id)
        .where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan, domain = row
    return ScanResponse(
        id=str(scan.id),
        domain_id=str(scan.domain_id),
        domain=domain,
        user_id=str(scan.user_id),
        scan_type=scan.scan_type,
        status=scan.status,
        modules_enabled=scan.modules_enabled,
        current_module=scan.current_module,
        progress_percentage=scan.progress_percentage,
        pages_crawled=scan.pages_crawled,
        requests_made=scan.requests_made,
        total_findings=scan.total_findings,
        critical_count=scan.critical_count,
        high_count=scan.high_count,
        medium_count=scan.medium_count,
        low_count=scan.low_count,
        info_count=scan.info_count,
        risk_score=scan.risk_score,
        grade=scan.grade,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
        error_message=scan.error_message,
        created_at=scan.created_at,
    )


@router.get("/{scan_id}/status", response_model=ScanStatus)
async def get_scan_status(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time scan status."""
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    return ScanStatus(
        scan_id=str(scan.id),
        status=scan.status,
        current_module=scan.current_module,
        progress_percentage=scan.progress_percentage,
        pages_crawled=scan.pages_crawled,
        requests_made=scan.requests_made,
        estimated_completion=scan.estimated_completion,
    )


@router.post("/{scan_id}/cancel")
async def cancel_scan(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running scan."""
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status not in ("queued", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel scan in {scan.status} state",
        )

    scan.status = "cancelled"
    scan.completed_at = datetime.now(timezone.utc)

    # Revoke celery task
    from app.workers.celery_app import celery_app

    if scan.celery_task_id:
        celery_app.control.revoke(scan.celery_task_id, terminate=True, signal="SIGKILL")
        logger.info(f"Revoked Celery task {scan.celery_task_id}")
    else:
        logger.warning(f"No celery_task_id for scan {scan_id}")

    await db.commit()
    return {"message": "Scan cancelled"}


@router.get("/{scan_id}/logs")
async def get_scan_logs(
    scan_id: str,
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get real-time scan logs."""
    # Verify ownership
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    scan_logger = ScanLogger(scan_id)
    logs = scan_logger.get_logs(offset, limit)
    total = scan_logger.get_total_count()
    scan_logger.close()

    return {
        "logs": logs,
        "total": total,
        "has_more": offset + len(logs) < total,
    }
