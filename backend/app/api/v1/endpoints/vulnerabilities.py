"""
SafeScan — Vulnerabilities Endpoints
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.vulnerability import Vulnerability
from app.models.scan import Scan
from app.schemas.vulnerability import (
    VulnerabilityResponse,
    VulnerabilityFilters,
    VulnerabilitySummary,
)

router = APIRouter()


@router.get("/")
async def list_vulnerabilities(
    filters: VulnerabilityFilters = Depends(),
    scan_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List vulnerabilities with optional filters."""
    base_query = (
        select(Vulnerability)
        .join(Scan, Vulnerability.scan_id == Scan.id)
        .where(Scan.user_id == uuid.UUID(current_user["sub"]))
    )

    if scan_id:
        base_query = base_query.where(Vulnerability.scan_id == uuid.UUID(scan_id))
    if filters.severity:
        base_query = base_query.where(Vulnerability.severity == filters.severity)
    if filters.module:
        base_query = base_query.where(Vulnerability.module == filters.module)
    if filters.owasp_category:
        base_query = base_query.where(
            Vulnerability.owasp_category == filters.owasp_category
        )
    if filters.is_false_positive is not None:
        base_query = base_query.where(
            Vulnerability.false_positive == filters.is_false_positive
        )
    if filters.is_resolved is not None:
        base_query = base_query.where(Vulnerability.is_resolved == filters.is_resolved)

    result = await db.execute(base_query.order_by(Vulnerability.created_at.desc()))
    vulns = result.scalars().all()

    return vulns


@router.get("/{vuln_id}", response_model=VulnerabilityResponse)
async def get_vulnerability(
    vuln_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get vulnerability details."""
    result = await db.execute(
        select(Vulnerability)
        .join(Scan, Vulnerability.scan_id == Scan.id)
        .where(
            Vulnerability.id == uuid.UUID(vuln_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    vuln = result.scalar_one_or_none()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")
    return vuln


@router.get("/summary/overall", response_model=VulnerabilitySummary)
async def get_vulnerability_summary(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get overall vulnerability statistics."""
    result = await db.execute(
        select(
            func.count(Vulnerability.id).label("total"),
            func.count(Vulnerability.id)
            .filter(Vulnerability.severity == "critical")
            .label("critical"),
            func.count(Vulnerability.id)
            .filter(Vulnerability.severity == "high")
            .label("high"),
            func.count(Vulnerability.id)
            .filter(Vulnerability.severity == "medium")
            .label("medium"),
            func.count(Vulnerability.id)
            .filter(Vulnerability.severity == "low")
            .label("low"),
            func.count(Vulnerability.id)
            .filter(Vulnerability.severity == "info")
            .label("info"),
        )
        .join(Scan, Vulnerability.scan_id == Scan.id)
        .where(
            Scan.user_id == uuid.UUID(current_user["sub"]),
            Vulnerability.false_positive == False,
        )
    )
    row = result.first()

    return VulnerabilitySummary(
        total=row.total or 0,
        critical=row.critical or 0,
        high=row.high or 0,
        medium=row.medium or 0,
        low=row.low or 0,
        info=row.info or 0,
        risk_score=None,  # Calculated separately
        grade=None,
    )


@router.post("/{vuln_id}/mark-false-positive")
async def mark_false_positive(
    vuln_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a vulnerability as false positive."""
    result = await db.execute(
        select(Vulnerability)
        .join(Scan, Vulnerability.scan_id == Scan.id)
        .where(
            Vulnerability.id == uuid.UUID(vuln_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    vuln = result.scalar_one_or_none()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    vuln.false_positive = True
    await db.commit()
    return {"message": "Marked as false positive"}


@router.post("/{vuln_id}/resolve")
async def resolve_vulnerability(
    vuln_id: str,
    note: str = Query(..., min_length=10),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a vulnerability as resolved."""
    from datetime import datetime, timezone

    result = await db.execute(
        select(Vulnerability)
        .join(Scan, Vulnerability.scan_id == Scan.id)
        .where(
            Vulnerability.id == uuid.UUID(vuln_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    vuln = result.scalar_one_or_none()
    if not vuln:
        raise HTTPException(status_code=404, detail="Vulnerability not found")

    vuln.is_resolved = True
    vuln.resolved_at = datetime.now(timezone.utc)
    vuln.resolution_note = note
    await db.commit()
    return {"message": "Vulnerability marked as resolved"}
