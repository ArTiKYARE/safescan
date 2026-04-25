"""
SafeScan — Authentication Endpoints
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
    get_current_user,
)
from app.core.config import settings
from app.core.email import send_email
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    TokenResponse,
    MFAVerify,
)
from app.services.audit import log_audit_event

router = APIRouter()


# --- Background Tasks Helpers ---


async def _send_welcome_email_bg(email: str, token: str):
    """Отправка письма в фоновом потоке, не блокируя ответ клиенту."""
    try:
        await asyncio.to_thread(
            send_email,
            to_email=email,
            subject="SafeScan — Подтверждение email",
            html_content=f"""
            <h2>Добро пожаловать в SafeScan!</h2>
            <p>Перейдите по ссылке для подтверждения email:</p>
            <a href="{settings.FRONTEND_URL}/verify-email?token={token}">Подтвердить email</a>
            <p><small>Ссылка действительна 24 часа.</small></p>
            """,
        )
    except Exception as e:
        # Логируем, но не прерываем регистрацию
        print(f"⚠️ Failed to send welcome email to {email}: {e}")


# --- Helper functions ---


def _extract_user_id(user_data: dict) -> str:
    return user_data.get("sub", "")


async def _get_user_from_db(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return user


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""

    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    # ✅ FIX 1: Хэширование в отдельном потоке (не блокирует event loop)
    pwd_hash = await asyncio.to_thread(hash_password, user_data.password)

    verification_token = str(uuid.uuid4())
    new_user = User(
        email=user_data.email,
        password_hash=pwd_hash,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email_verification_token=verification_token,
        email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=24),
        email_verified=True,  # Auto-verify in dev; disable in production
    )
    db.add(new_user)
    await db.flush()

    # ✅ FIX 2: Отправка письма в фоне через create_task
    asyncio.create_task(_send_welcome_email_bg(new_user.email, verification_token))

    await log_audit_event(
        db=db,
        user_id=new_user.id,
        action="USER_REGISTERED",
        details={"email": new_user.email},
    )

    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return JWT tokens."""

    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user:
        # Защита от timing-атак: фейковое хэширование при неверном email
        await asyncio.to_thread(hash_password, "dummy_password")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # ✅ FIX 3: Верификация пароля в отдельном потоке + безопасный try/except
    try:
        is_valid = await asyncio.to_thread(
            verify_password, credentials.password, user.password_hash
        )
    except Exception as e:
        # Предотвращает 500 ошибку при битых хэшах или ошибках bcrypt
        print(f"⚠️ Password verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error",
        )

    if not is_valid:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account blocked: {user.blocked_reason}",
        )

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox.",
        )

    if user.mfa_enabled:
        if not credentials.mfa_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="MFA token required",
                headers={"X-MFA-Required": "true"},
            )
        if not user.mfa_secret or not verify_totp(
            user.mfa_secret, credentials.mfa_token
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA token"
            )

    user.last_login = datetime.now(timezone.utc)
    user.failed_login_attempts = 0

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await log_audit_event(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        details={"ip": str(request.client.host) if request.client else "unknown"},
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    request_body: dict, db: AsyncSession = Depends(get_db)
):
    refresh_token_str = request_body.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required"
        )

    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    token_data = {
        "sub": payload.get("sub"),
        "email": payload.get("email"),
        "role": payload.get("role"),
    }
    new_access_token = create_access_token(token_data)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token_str,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/verify-email")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email_verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token"
        )

    if (
        user.email_verification_expires
        and user.email_verification_expires < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token expired"
        )

    user.email_verified = True
    user.email_verification_token = None

    await log_audit_event(
        db=db, user_id=user.id, action="EMAIL_VERIFIED", details={"email": user.email}
    )
    await db.commit()
    return {"message": "Email verified successfully"}


# --- MFA Endpoints (без изменений, работают корректно) ---
@router.post("/mfa/setup", response_model=dict)
async def setup_mfa(
    current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    user = await _get_user_from_db(db, _extract_user_id(current_user))
    secret = generate_totp_secret()
    totp_uri = get_totp_uri(secret, user.email)
    user.mfa_secret = secret
    await db.commit()
    return {
        "secret": secret,
        "totp_uri": totp_uri,
        "message": "Scan the QR code with your authenticator app",
    }


@router.post("/mfa/verify")
async def verify_mfa(
    mfa_data: MFAVerify,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_from_db(db, _extract_user_id(current_user))
    if not user.mfa_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA not initiated. Call /mfa/setup first.",
        )
    if verify_totp(user.mfa_secret, mfa_data.totp_code):
        user.mfa_enabled = True
        await log_audit_event(db=db, user_id=user.id, action="MFA_ENABLED")
        await db.commit()
        return {"message": "MFA enabled successfully"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code"
    )


@router.post("/mfa/disable")
async def disable_mfa(
    mfa_data: MFAVerify,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_from_db(db, _extract_user_id(current_user))
    if not user.mfa_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="MFA is not enabled"
        )
    if verify_totp(user.mfa_secret, mfa_data.totp_code):
        user.mfa_enabled = False
        user.mfa_secret = None
        await log_audit_event(db=db, user_id=user.id, action="MFA_DISABLED")
        await db.commit()
        return {"message": "MFA disabled"}
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid TOTP code"
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    return {"message": "Logged out successfully"}
