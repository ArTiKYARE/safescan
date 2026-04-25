"""
SafeScan — Report Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ReportSummary(BaseModel):
    """Executive summary of a scan report."""
    scan_id: str
    domain: str
    scan_date: datetime
    scan_duration: str
    total_findings: int
    critical: int
    high: int
    medium: int
    low: int
    info: int
    risk_score: float
    grade: str


class ReportResponse(BaseModel):
    """Full report response."""
    metadata: dict
    summary: ReportSummary
    vulnerabilities: List[dict]
    compliance: dict
    recommendations: List[str]
