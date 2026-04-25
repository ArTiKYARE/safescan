"""
SafeScan — Domains Endpoints
"""

import uuid
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.domain import Domain
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.api_key import APIKey
from app.schemas.domain import (
    DomainCreate,
    DomainResponse,
    DomainVerify,
    DomainVerificationStatus,
)
from app.schemas.api_key import APIKeyWithSecret
from app.services.audit import log_audit_event
from app.services.domain_verification import DomainVerificationService

router = APIRouter()


@router.post("/", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(
    domain_data: DomainCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a domain for verification. Admins auto-verify. API token method auto-verifies."""
    user_role = current_user.get("role", "viewer")
    is_admin = user_role in ("admin", "security_auditor")

    # Check if domain already exists for the user
    result = await db.execute(
        select(Domain).where(
            Domain.user_id == uuid.UUID(current_user["sub"]),
            Domain.domain == domain_data.domain.lower(),
        )
    )
    existing = result.scalar_one_or_none()

    # If domain exists and uses api_token method, regenerate API key instead of error
    if existing and existing.verification_method == "api_token":
        # Generate a new API key
        api_key_secret = f"sk_{domain_data.domain.lower()}_{secrets.token_urlsafe(32)}"
        api_key_prefix = api_key_secret[:12]
        env_line = f'SAFESCAN_API_KEY="{api_key_secret}"'

        # Store the new key in the database
        new_key = APIKey(
            user_id=uuid.UUID(current_user["sub"]),
            name=f"{domain_data.domain.lower()} (regenerated)",
            key_prefix=api_key_prefix,
            key_hash=secrets.token_urlsafe(64),
            secret=api_key_secret,
            scopes="scan:read scan:write domain:read",
            is_active=True,
        )
        db.add(new_key)
        await db.flush()

        await log_audit_event(
            db=db,
            user_id=uuid.UUID(current_user["sub"]),
            action="API_KEY_REGENERATED",
            resource_type="domain",
            resource_id=existing.id,
            details={
                "domain": domain_data.domain,
                "api_key_prefix": api_key_prefix,
            },
        )

        await db.commit()

        return {
            "id": str(existing.id),
            "domain": existing.domain,
            "is_verified": existing.is_verified,
            "verification_method": existing.verification_method,
            "verified_at": existing.verified_at,
            "scan_consent_required": existing.scan_consent_required,
            "created_at": existing.created_at,
            "updated_at": existing.updated_at,
            "api_key": api_key_secret,
            "api_key_prefix": api_key_prefix,
            "env_line": env_line,
            "_regenerated": True,
        }

    # If domain exists with a different method, return conflict
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Domain already added with a different verification method. Delete it first to add with a new method.",
        )

    # Generate verification token
    verification_token = secrets.token_urlsafe(32)

    # API token method — generate key but DON'T auto-verify
    is_api_token = domain_data.verification_method == "api_token"

    # Create domain record
    new_domain = Domain(
        domain=domain_data.domain.lower(),
        user_id=uuid.UUID(current_user["sub"]),
        verification_method=domain_data.verification_method,  # Always store the method
        verification_token=verification_token if not is_admin else None,
        dns_record_name="_safescan-verify" if not is_admin else None,
        dns_record_value=verification_token if not is_admin else None,
        verification_file_path=(
            "/.well-known/safescan-verify.txt" if not is_admin else None
        ),
        is_verified=is_admin,  # Only admins auto-verify
        verified_at=datetime.now(timezone.utc) if is_admin else None,
    )
    db.add(new_domain)
    await db.flush()

    # Generate API key for api_token method and SAVE to DB immediately
    api_key_secret = None
    api_key_prefix = None
    env_line = None

    if is_api_token:
        import hashlib

        api_key_secret = f"sk_{domain_data.domain.lower()}_{secrets.token_urlsafe(32)}"
        api_key_prefix = api_key_secret[:12]
        env_line = f'SAFESCAN_API_KEY="{api_key_secret}"'

        # Create and save API key record immediately
        api_key_record = APIKey(
            user_id=uuid.UUID(current_user["sub"]),
            name=f"{domain_data.domain.lower()} (auto-generated)",
            key_prefix=api_key_prefix,
            key_hash=hashlib.sha256(api_key_secret.encode()).hexdigest(),
            secret=api_key_secret,
            scopes="scan:read,scan:write,domain:read",
            is_active=True,
        )
        db.add(api_key_record)

    # Send verification email if method is email
    if domain_data.verification_method == "email":
        from app.core.email import send_email, get_verification_email_html

        await send_email(
            to_email=f"admin@{domain_data.domain}",
            subject="SafeScan — Domain Verification",
            html_content=get_verification_email_html(
                verification_token, domain_data.domain
            ),
        )
        new_domain.verification_email_sent_to = f"admin@{domain_data.domain}"
        new_domain.verification_email_sent_at = datetime.now(timezone.utc)

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="DOMAIN_ADDED",
        resource_type="domain",
        resource_id=new_domain.id,
        details={
            "domain": domain_data.domain,
            "method": domain_data.verification_method,
            "api_key_generated": is_api_token,
        },
    )

    await db.commit()
    await db.refresh(new_domain)

    # Return domain with optional API key info in response
    response_data = {
        "id": str(new_domain.id),
        "domain": new_domain.domain,
        "is_verified": new_domain.is_verified,
        "verification_method": new_domain.verification_method,
        "verified_at": new_domain.verified_at,
        "scan_consent_required": new_domain.scan_consent_required,
        "created_at": new_domain.created_at,
        "updated_at": new_domain.updated_at,
    }
    if is_api_token:
        response_data["api_key"] = api_key_secret
        response_data["api_key_prefix"] = api_key_prefix
        response_data["env_line"] = env_line

    return response_data


@router.get("/")
async def list_domains(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all domains for current user."""
    result = await db.execute(
        select(Domain)
        .where(Domain.user_id == uuid.UUID(current_user["sub"]))
        .order_by(Domain.created_at.desc())
    )
    domains = result.scalars().all()

    return domains


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get domain details."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    return domain


@router.get("/{domain_id}/verification-status", response_model=DomainVerificationStatus)
async def get_verification_status(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get domain verification status and instructions."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    instructions = ""
    if domain.verification_method == "api_token":
        instructions = (
            f"Добавьте API ключ в конфигурацию вашего сайта для подтверждения владения.\n\n"
            f"📋 Что нужно сделать:\n"
            f"  1. Откройте файл .env вашего проекта\n"
            f'  2. Добавьте строку: SAFESCAN_API_KEY="<ваш_ключ>"\n'
            f"  3. Перезапустите ваш сайт\n\n"
            f"💡 API ключ также доступен во вкладке «API ключи» —\n"
            f"  вы можете скопировать его в любое время.\n\n"
            f"⏱️ После добавления ключа SafeScan автоматически проверит\n"
            f"  наличие ключа каждые 5 секунд. Также вы можете\n"
            f"  нажать кнопку «Проверить сейчас»."
        )
    elif domain.verification_method == "dns":
        instructions = (
            f"Добавьте TXT-запись в DNS вашего домена.\n\n"
            f"📋 Данные записи:\n"
            f"  Имя (Host):  {domain.dns_record_name}.{domain.domain}\n"
            f"  Тип:         TXT\n"
            f"  Значение:    {domain.dns_record_value}\n\n"
            f"📌 Где найти настройки DNS:\n"
            f"  • Cloudflare: Dashboard → DNS → Records → Add Record\n"
            f"  • Reg.ru: Управление DNS → Добавить запись\n"
            f"  • GoDaddy: DNS Management → Add Record\n"
            f"  • Namecheap: Advanced DNS → Add New Record\n\n"
            f"💡 Важно:\n"
            f"  • В поле «Имя» укажите: {domain.dns_record_name}\n"
            f"    (без .{domain.domain} — многие панели добавляют домен автоматически)\n"
            f"  • В поле «Значение/TTL» укажите: {domain.dns_record_value}\n"
            f"  • Тип записи: TXT\n"
            f"  • TTL: можно оставить по умолчанию (Auto или 3600)\n\n"
            f"⏱️ После добавления записи DNS может обновляться от 1 до 60 минут.\n"
            f"SafeScan автоматически проверяет наличие записи каждые 5 секунд."
        )
    elif domain.verification_method == "file":
        instructions = (
            f"Создайте текстовый файл на вашем сайте.\n\n"
            f"📋 Путь и содержимое:\n"
            f"  URL:  https://{domain.domain}{domain.verification_file_path}\n"
            f"  Содержимое: {domain.verification_token}\n\n"
            f"📌 Как создать:\n"
            f"  1. Создайте директорию: .well-known/ в корне сайта\n"
            f"  2. Создайте файл: safescan-verify.txt\n"
            f"  3. Вставьте содержимое (точно, без пробелов и переносов)\n"
            f"  4. Убедитесь, что файл доступен по URL выше\n\n"
            f"💡 Для nginx добавьте в конфиг:\n"
            f"  location /.well-known/ {{\n"
            f"    allow all;\n"
            f"  }}\n\n"
            f"⏱️ SafeScan автоматически проверяет наличие файла каждые 5 секунд."
        )

    return DomainVerificationStatus(
        domain_id=str(domain.id),
        domain=domain.domain,
        is_verified=domain.is_verified,
        verification_method=domain.verification_method,
        verification_token=domain.verification_token,
        dns_record_name=domain.dns_record_name,
        dns_record_value=domain.dns_record_value,
        verification_file_path=domain.verification_file_path,
        verification_email_sent_to=domain.verification_email_sent_to,
        instructions=instructions,
    )


@router.post("/{domain_id}/verify", response_model=dict)
async def verify_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger domain verification check. Generates API key on success."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    if domain.is_verified:
        # Check if API key already exists for this domain
        key_result = await db.execute(
            select(APIKey).where(
                APIKey.user_id == uuid.UUID(current_user["sub"]),
                APIKey.name.ilike(f"{domain.domain}%"),
            )
        )
        existing_key = key_result.scalar_one_or_none()
        return {
            "message": "Domain already verified",
            "is_verified": True,
            "api_key": existing_key.key_prefix + "..." if existing_key else None,
        }

    # Run verification
    service = DomainVerificationService()
    is_verified = await service.verify(domain)

    if is_verified:
        domain.is_verified = True
        domain.verified_at = datetime.now(timezone.utc)
        domain.last_reverification = datetime.now(timezone.utc)

        # Generate API key for this domain
        import hashlib

        api_key_secret = f"sk_{domain.domain}_{secrets.token_urlsafe(32)}"
        api_key_prefix = api_key_secret[:12]

        new_key = APIKey(
            user_id=uuid.UUID(current_user["sub"]),
            name=f"{domain.domain} (auto-generated)",
            key_prefix=api_key_prefix,
            key_hash=hashlib.sha256(api_key_secret.encode()).hexdigest(),
            secret=api_key_secret,
            scopes="scan:read,scan:write,domain:read",
            is_active=True,
        )
        db.add(new_key)
        await db.flush()

        await log_audit_event(
            db=db,
            user_id=uuid.UUID(current_user["sub"]),
            action="DOMAIN_VERIFIED",
            resource_type="domain",
            resource_id=domain.id,
            details={
                "domain": domain.domain,
                "api_key_prefix": api_key_prefix,
            },
        )

        await db.commit()

        return {
            "message": "Domain verified successfully",
            "is_verified": True,
            "api_key": api_key_secret,
            "api_key_prefix": api_key_prefix,
            "env_line": f'SAFESCAN_API_KEY="{api_key_secret}"',
        }
    else:
        return {
            "message": "Verification failed. Please ensure the verification record is in place.",
            "is_verified": False,
        }


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a domain and all associated scans."""
    result = await db.execute(
        select(Domain).where(
            Domain.id == uuid.UUID(domain_id),
            Domain.user_id == uuid.UUID(current_user["sub"]),
        )
    )
    domain = result.scalar_one_or_none()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")

    await log_audit_event(
        db=db,
        user_id=uuid.UUID(current_user["sub"]),
        action="DOMAIN_DELETED",
        resource_type="domain",
        resource_id=domain.id,
        details={"domain": domain.domain},
    )

    await db.delete(domain)
    await db.commit()
