"""
SafeScan — Reports Endpoints
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.services.report_generator import ReportGeneratorService

router = APIRouter()


@router.get("/{scan_id}/json")
async def get_report_json(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scan report as JSON."""
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not available for scan in {scan.status} state",
        )

    generator = ReportGeneratorService(db)
    report = await generator.generate_json(scan)
    return report


@router.get("/{scan_id}/pdf")
async def get_report_pdf(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scan report as PDF."""
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not available for scan in {scan.status} state",
        )

    generator = ReportGeneratorService(db)
    pdf_bytes = await generator.generate_pdf(scan)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="safescan-report-{scan_id}.pdf"',
        },
    )


@router.get("/{scan_id}/html")
async def get_report_html(
    scan_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get scan report as HTML."""
    result = await db.execute(
        select(Scan).where(
            Scan.id == uuid.UUID(scan_id),
            Scan.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")

    if scan.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Report not available for scan in {scan.status} state",
        )

    generator = ReportGeneratorService(db)
    html = await generator.generate_html(scan)
    return Response(content=html, media_type="text/html")
