"""
SafeScan — Domain Verification Endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Domain
from app.services.domain_verification import DomainVerificationService

router = APIRouter()


@router.get("/check-dns/{domain_id}")
async def check_dns_verification(
    domain_id: str,  # 👈 Принимаем UUID домена, а не строку
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check DNS TXT record for domain verification."""
    
    # 1. Находим домен в БД
    try:
        domain_uuid = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    
    result = await db.execute(
        select(Domain).where(
            Domain.id == domain_uuid,
            Domain.user_id == uuid.UUID(current_user["sub"])  # Проверка прав
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found or access denied")
    
    # 2. Вызываем сервис с токеном
    service = DomainVerificationService()
    verification_result = await service.check_dns(
        domain.domain, 
        expected_token=domain.verification_token  # 👈 КЛЮЧЕВОЕ: передаём токен!
    )
    
    # 3. Если верификация успешна — обновляем статус в БД
    if verification_result["verified"]:
        domain.is_verified = True
        domain.verification_method = "dns"
        await db.commit()
    
    return verification_result


@router.get("/check-file/{domain_id}")
async def check_file_verification(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check verification file on domain."""
    
    # 1. Находим домен в БД
    try:
        domain_uuid = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    
    result = await db.execute(
        select(Domain).where(
            Domain.id == domain_uuid,
            Domain.user_id == uuid.UUID(current_user["sub"])
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found or access denied")
    
    # 2. Вызываем сервис с токеном
    service = DomainVerificationService()
    verification_result = await service.check_file(
        domain.domain,
        expected_token=domain.verification_token  # 👈 Передаём токен!
    )
    
    # 3. Если верификация успешна — обновляем статус
    if verification_result["verified"]:
        domain.is_verified = True
        domain.verification_method = "file"
        await db.commit()
    
    return verification_result


@router.post("/verify-email/{domain_id}")
async def verify_email_token(
    domain_id: str,
    token: str,  # Токен из ссылки в письме
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Verify domain via email token (user clicked link in email)."""
    
    try:
        domain_uuid = uuid.UUID(domain_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain ID format")
    
    result = await db.execute(
        select(Domain).where(
            Domain.id == domain_uuid,
            Domain.user_id == uuid.UUID(current_user["sub"])
        )
    )
    domain = result.scalar_one_or_none()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found or access denied")
    
    # Сравниваем токен из ссылки с сохранённым
    if domain.api_verification_token and token == domain.api_verification_token:
        domain.is_verified = True
        domain.verification_method = "email"
        domain.verified_at = None  # Будет установлено при commit
        await db.commit()
        return {"verified": True, "message": "Domain verified via email"}
    
    raise HTTPException(status_code=400, detail="Invalid or expired verification token")