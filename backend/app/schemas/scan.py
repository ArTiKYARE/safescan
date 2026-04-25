"""
SafeScan — Scan Schemas
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BaseSchema


class ScanCreate(BaseModel):
    """Schema for initiating a scan."""
    domain_id: str
    scan_type: str = Field(default="full", pattern="^(full|quick|custom)$")
    modules: Optional[List[str]] = None  # Specific modules for 'custom' type
    consent_acknowledged: bool = Field(
        ...,
        description="User must acknowledge ownership consent before scanning",
    )


class ScanFilters(BaseModel):
    """Filters for listing scans."""
    status: Optional[str] = None
    scan_type: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class ScanResponse(BaseSchema):
    """Scan details response."""
    id: str
    domain_id: str
    domain: str = ""  # Joined from Domain table
    user_id: str
    scan_type: str
    status: str
    modules_enabled: Optional[List[str]]
    current_module: Optional[str]
    progress_percentage: int
    pages_crawled: int
    requests_made: int
    total_findings: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    risk_score: Optional[float]
    grade: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str] = None
    created_at: datetime
    # Billing
    cost: float = 0.0
    free_scans_remaining: int = 0

    class Config:
        from_attributes = True


class ScanStatus(BaseSchema):
    """Real-time scan status."""
    scan_id: str
    status: str
    current_module: Optional[str]
    progress_percentage: int
    pages_crawled: int
    requests_made: int
    estimated_completion: Optional[datetime]


class ScanSummary(BaseSchema):
    """Brief scan summary for lists."""
    id: str
    domain: str
    scan_type: str
    status: str
    total_findings: int
    critical_count: int
    high_count: int
    grade: Optional[str]
    completed_at: Optional[datetime]
