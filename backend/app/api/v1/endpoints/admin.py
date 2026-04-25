import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.core.database import get_db
from app.core.security import get_current_user, hash_password
from app.models.user import User
from app.models.domain import Domain
from app.services.audit import log_audit_event

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Ensure user is admin."""
    if current_user.get("role") not in ("admin", "security_auditor"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _user_to_dict(u: User) -> dict:
    return {
        "id": str(u.id),
        "email": u.email,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "role": u.role,
        "is_active": u.is_active,
        "is_blocked": u.is_blocked,
        "blocked_reason": u.blocked_reason,
        "failed_login_attempts": u.failed_login_attempts,
        "email_verified": u.email_verified,
        "mfa_enabled": u.mfa_enabled,
        "balance": u.balance,
        "last_login": u.last_login.isoformat() if u.last_login else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "updated_at": u.updated_at.isoformat() if u.updated_at else None,
    }


def _domain_to_dict(d: Domain) -> dict:
    return {
        "id": str(d.id),
        "domain": d.domain,
        "is_verified": d.is_verified,
        "verification_method": d.verification_method,
        "verified_at": d.verified_at.isoformat() if d.verified_at else None,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    }


@router.get("/users")
async def list_all_users(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    return [_user_to_dict(u) for u in result.scalars().all()]


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    role: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    is_blocked: Optional[bool] = Query(None),
    blocked_reason: Optional[str] = Query(None),
    new_password: Optional[str] = Query(None),
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user properties (admin only)."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent self-lockout
    if str(user.id) == current_user["sub"] and is_blocked:
        raise HTTPException(status_code=400, detail="Cannot block yourself")

    changes = []
    if role is not None and role in ("viewer", "operator", "admin", "security_auditor"):
        user.role = role
        changes.append(f"role → {role}")

    if is_active is not None:
        user.is_active = is_active
        changes.append(f"is_active → {is_active}")

    if is_blocked is not None:
        user.is_blocked = is_blocked
        user.blocked_reason = blocked_reason if is_blocked else None
        changes.append(f"is_blocked → {is_blocked}")

    if new_password:
        user.password_hash = hash_password(new_password)
        changes.append("password changed")
        user.failed_login_attempts = 0
        user.locked_until = None

    if changes:
        await log_audit_event(
            db=db,
            user_id=uuid.UUID(current_user["sub"]),
            action="ADMIN_USER_UPDATED",
            resource_type="user",
            resource_id=user.id,
            details={"target_user": user.email, "changes": changes},
        )

    await db.commit()
    return {"message": "User updated", "changes": changes}


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user (admin only). Cannot delete yourself."""
    if str(uuid.UUID(user_id)) == current_user["sub"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="ADMIN_USER_DELETED",
        resource_type="user",
        resource_id=user.id,
        details={"target_user": user.email},
    )

    await db.delete(user)
    await db.commit()


@router.get("/stats")
async def get_admin_stats(
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get platform statistics (admin only)."""
    role_result = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    roles = dict(role_result.all())

    total_result = await db.execute(select(func.count(User.id)))
    total_users = total_result.scalar()

    return {
        "total_users": total_users,
        "by_role": roles,
    }


@router.get("/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed user info (admin only)."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Count domains and scans
    domains_result = await db.execute(
        select(func.count(Domain.id)).where(Domain.user_id == user.id)
    )
    domain_count = domains_result.scalar()

    from app.models.scan import Scan
    scans_result = await db.execute(
        select(func.count(Scan.id)).where(Scan.user_id == user.id)
    )
    scan_count = scans_result.scalar()

    return {
        **_user_to_dict(user),
        "domain_count": domain_count,
        "scan_count": scan_count,
    }


@router.get("/users/{user_id}/domains")
async def get_user_domains(
    user_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get all domains of a user (admin only)."""
    result = await db.execute(
        select(Domain).where(Domain.user_id == uuid.UUID(user_id)).order_by(Domain.created_at.desc())
    )
    domains = result.scalars().all()
    return [_domain_to_dict(d) for d in domains]


@router.post("/users/{user_id}/domains/{domain_id}/approve")
async def approve_domain(
    user_id: str,
    domain_id: str,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Approve (verify) a user's domain (admin only)."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.user_id == uuid.UUID(user_id),
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if domain.is_verified:
        return {"message": "Domain already verified", "is_verified": True}

    domain.is_verified = True
    domain.verified_at = datetime.now(timezone.utc)
    domain.last_reverification = datetime.now(timezone.utc)

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="ADMIN_DOMAIN_APPROVED",
        resource_type="domain",
        resource_id=domain.id,
        details={"domain": domain.domain, "owner": str(domain.user_id)},
    )

    await db.commit()
    return {"message": "Domain approved", "is_verified": True}


@router.post("/users/{user_id}/balance")
async def add_user_balance(
    user_id: str,
    amount: float,
    description: Optional[str] = None,
    current_user: dict = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add balance to a user's account (admin only)."""
    amount = round(amount, 2)

    # Find target user
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Credit balance
    user.balance += amount

    # Create transaction record
    from app.models.transaction import Transaction
    txn = Transaction(
        user_id=uuid.UUID(user_id),
        amount=amount,
        currency="RUB",
        type="admin_adjustment",
        status="completed",
        payment_method="manual",
        description=description or f"Пополнение баланса администратором: {current_user.get('email')}",
    )
    db.add(txn)

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="MANUAL_TOPUP",
        resource_type="transaction",
        resource_id=txn.id,
        details={"target_user": user.email, "amount": amount},
    )

    await db.commit()
    return {
        "message": f"Баланс пользователя {user.email} пополнен на {amount} RUB",
        "new_balance": user.balance,
    }
