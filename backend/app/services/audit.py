"""
SafeScan — Audit Logging Service
"""

import hashlib
import json
import uuid
from typing import Optional, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.audit_log import AuditLog


async def log_audit_event(
    db: AsyncSession,
    user_id: Optional[uuid.UUID],
    action: str,
    resource_type: Optional[str] = None,
    resource_id: Optional[uuid.UUID] = None,
    details: Optional[dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    """
    Create an immutable audit log entry with hash chaining.
    
    Each row's hash includes the previous row's hash, creating a chain
    that makes tampering detectable.
    """
    # Get the last row hash
    result = await db.execute(
        select(AuditLog.row_hash)
        .order_by(AuditLog.created_at.desc())
        .limit(1)
    )
    last_hash = result.scalar_one_or_none()

    # Create new audit log entry
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        prev_hash=last_hash,
    )

    # Calculate row hash: SHA-256(prev_hash + action + user_id + timestamp + details)
    hash_data = json.dumps({
        "prev_hash": last_hash,
        "action": action,
        "user_id": str(user_id) if user_id else None,
        "resource_type": resource_type,
        "resource_id": str(resource_id) if resource_id else None,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, sort_keys=True)
    entry.row_hash = hashlib.sha256(hash_data.encode()).hexdigest()

    db.add(entry)
    return entry


async def verify_audit_chain(db: AsyncSession) -> dict:
    """
    Verify the integrity of the audit log chain.
    
    Returns status and any broken links.
    """
    result = await db.execute(
        select(AuditLog)
        .order_by(AuditLog.created_at.asc())
    )
    logs = result.scalars().all()

    broken_links = []
    prev_hash = None

    for i, log in enumerate(logs):
        # Recalculate hash
        hash_data = json.dumps({
            "prev_hash": log.prev_hash,
            "action": log.action,
            "user_id": str(log.user_id) if log.user_id else None,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "details": log.details,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
        }, sort_keys=True)
        expected_hash = hashlib.sha256(hash_data.encode()).hexdigest()

        if log.row_hash != expected_hash:
            broken_links.append({
                "log_id": str(log.id),
                "index": i,
                "expected_hash": expected_hash,
                "actual_hash": log.row_hash,
            })

        prev_hash = log.row_hash

    return {
        "total_entries": len(logs),
        "valid": len(broken_links) == 0,
        "broken_links": broken_links,
    }
