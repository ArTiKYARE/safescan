"""
SafeScan — Billing Endpoints (balance, top-up, YooKassa)
"""

import httpx
import uuid
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from app.schemas.billing import BalanceResponse, TopUpRequest, TransactionResponse
from app.services.audit import log_audit_event

router = APIRouter()

# YooKassa config (set via env vars)
import os

YOOKASSA_SHOP_ID = os.getenv("YOOKASSA_SHOP_ID", "")
YOOKASSA_SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY", "")
YOOKASSA_RETURN_URL = os.getenv("YOOKASSA_RETURN_URL", "http://localhost:3000/account")


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user balance."""
    result = await db.execute(
        select(User).where(User.id == uuid.UUID(current_user["sub"]))
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return BalanceResponse(balance=user.balance)


@router.get("/transactions", response_model=list[TransactionResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user transactions."""
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == uuid.UUID(current_user["sub"]))
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    transactions = result.scalars().all()
    return transactions


@router.post("/topup")
async def create_topup(
    data: TopUpRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a top-up request via YooKassa."""
    import logging
    import httpx
    import base64

    logger = logging.getLogger(__name__)

    # Проверка настроек ЮKassa
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        return {
            "message": "ЮKassa не настроена. Пополнение обрабатывается в ручном режиме через админ-панель.",
            "status": "pending",
        }

    amount = round(data.amount, 2)

    # ✅ Генерируем уникальный ключ идемпотентности (с "ence"!)
    idempotency_key = str(uuid.uuid4())

    # ✅ Basic Auth для ЮKassa
    auth_str = base64.b64encode(
        f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}".encode()
    ).decode()

    payment_data = {
        "amount": {
            "value": f"{amount:.2f}",
            "currency": "RUB",
        },
        "confirmation": {
            "type": "redirect",
            "return_url": YOOKASSA_RETURN_URL,
        },
        "capture": True,
        "description": f"Пополнение баланса SafeScan",
        "metadata": {
            "user_id": current_user["sub"],
            "type": "topup",
        },
    }

    try:
        # ✅ Используем httpx.AsyncClient — нативная асинхронность
        async with httpx.AsyncClient(timeout=30.0, verify=True) as client:
            logger.info(
                f"Sending YooKassa payment request for user {current_user['sub']}, amount {amount} RUB"
            )

            response = await client.post(
                "https://api.yookassa.ru/v3/payments",
                json=payment_data,
                headers={
                    "Content-Type": "application/json",
                    "Idempotence-Key": idempotency_key,  # ✅ Правильное написание!
                    "Authorization": f"Basic {auth_str}",
                    "User-Agent": "SafeScan/1.0 (+https://safescanget.ru)",
                },
            )

            logger.info(
                f"YooKassa response: {response.status_code} - {response.text[:200]}"
            )

            # Обработка ошибок ответа
            if response.status_code not in (200, 201):
                error_detail = (
                    response.text[:300] if response.text else "No response body"
                )
                logger.error(
                    f"YooKassa HTTP error {response.status_code}: {error_detail}"
                )
                raise HTTPException(
                    status_code=502,
                    detail=f"ЮKassa error (HTTP {response.status_code}): {error_detail}",
                )

            payment = response.json()

            # Валидация ответа
            if "id" not in payment or "confirmation" not in payment:
                logger.error(f"Invalid YooKassa response: {payment}")
                raise HTTPException(
                    status_code=502,
                    detail="Некорректный ответ от ЮKassa: отсутствуют обязательные поля",
                )

        # ✅ Создаём запись транзакции в БД
        txn = Transaction(
            user_id=uuid.UUID(current_user["sub"]),
            amount=amount,
            currency="RUB",
            type="yookassa",
            status="pending",
            payment_method="yookassa",
            payment_id=payment["id"],
            confirmation_url=payment["confirmation"]["confirmation_url"],
            description=f"Пополнение через ЮKassa: {amount} RUB",
        )
        db.add(txn)
        await db.commit()
        await db.refresh(txn)

        # ✅ Логирование аудита
        await log_audit_event(
            db=db,
            user_id=uuid.UUID(current_user["sub"]),
            action="PAYMENT_INITIATED",
            resource_type="transaction",
            resource_id=txn.id,
            details={
                "payment_id": payment["id"],
                "amount": amount,
                "idempotency_key": idempotency_key,
            },
        )

        logger.info(
            f"Payment created: {payment['id']}, confirmation_url: {payment['confirmation']['confirmation_url']}"
        )

        return {
            "status": "pending",
            "payment_id": payment["id"],
            "confirmation_url": payment["confirmation"]["confirmation_url"],
            "message": "Перенаправляем на ЮKassa для оплаты...",
        }

    # ✅ Обработка сетевых ошибок
    except httpx.RequestError as e:
        logger.error(f"YooKassa request error: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка сети при подключении к ЮKassa: {str(e)}",
        )

    # ✅ Обработка ошибок HTTP-статусов
    except httpx.HTTPStatusError as e:
        logger.error(
            f"YooKassa HTTP status error: {e.response.status_code} - {e.response.text[:200]}"
        )
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка ЮKassa: HTTP {e.response.status_code}",
        )

    # ✅ Обработка ошибок БД
    except Exception as e:
        import traceback

        logger.error(f"YooKassa unexpected error: {type(e).__name__}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=502,
            detail=f"Ошибка подключения к ЮKassa: {str(e)}",
        )


@router.post("/webhook/yookassa")
async def yookassa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """YooKassa webhook handler — с детальным логированием для отладки."""
    import logging
    import json

    logger = logging.getLogger(__name__)

    try:
        raw_body = await request.body()
        logger.info(f"🔍 Webhook raw body: {raw_body.decode('utf-8')[:500]}")

        body = await request.json()
        logger.info(
            f"🔍 Webhook parsed: event={body.get('event')}, object keys={list(body.get('object', {}).keys())}"
        )

        event_type = body.get("event", "")
        payment_obj = body.get("object", {})
        payment_id = payment_obj.get("id")
        payment_status = payment_obj.get("status", "")
        amount_value = payment_obj.get("amount", {}).get("value", "0")
        metadata = payment_obj.get("metadata", {})
        user_id_raw = metadata.get("user_id")

        logger.info(
            f"🔍 Extracted: payment_id={payment_id}, status={payment_status}, user_id_raw={user_id_raw}, amount={amount_value}"
        )

        # Валидация
        if not user_id_raw or not payment_id:
            logger.warning(
                f"❌ Webhook missing fields: user_id={user_id_raw}, payment_id={payment_id}"
            )
            return {"status": "ignored", "reason": "missing_metadata"}

        # Парсинг UUID (может быть строкой или уже UUID)
        try:
            user_id = (
                uuid.UUID(user_id_raw) if isinstance(user_id_raw, str) else user_id_raw
            )
        except (ValueError, AttributeError) as e:
            logger.error(f"❌ Failed to parse user_id '{user_id_raw}': {e}")
            return {"status": "error", "reason": "invalid_user_id"}

        # Поиск транзакции
        result = await db.execute(
            select(Transaction)
            .where(
                Transaction.payment_id == payment_id,
                Transaction.user_id == user_id,
            )
            .with_for_update()
        )
        txn = result.scalar_one_or_none()

        if not txn:
            logger.warning(
                f"❌ Transaction not found: payment_id={payment_id}, user_id={user_id}"
            )
            # Попробуем найти только по payment_id (для отладки)
            debug_result = await db.execute(
                select(Transaction).where(Transaction.payment_id == payment_id)
            )
            debug_txn = debug_result.scalar_one_or_none()
            if debug_txn:
                logger.info(
                    f"🔍 Found transaction with different user_id: {debug_txn.user_id}"
                )
            return {"status": "not_found"}

        logger.info(f"✅ Found transaction: id={txn.id}, current_status={txn.status}")

        # Обработка успешной оплаты — проверяем несколько возможных статусов
        if (
            payment_status in ("succeeded", "paid", "waiting_for_capture")
            and txn.status != "completed"
        ):
            logger.info(
                f"💰 Processing payment completion: {payment_status} → completed"
            )

            txn.status = "completed"
            txn.updated_at = datetime.now(timezone.utc)

            # Обновление баланса
            user_result = await db.execute(
                select(User).where(User.id == user_id).with_for_update()
            )
            user = user_result.scalar_one_or_none()

            if user:
                old_balance = user.balance
                user.balance += float(amount_value)
                logger.info(
                    f"💰 Balance updated: {user.email} {old_balance} → {user.balance} (+{amount_value})"
                )
            else:
                logger.error(f"❌ User not found: {user_id}")

            await log_audit_event(
                db=db,
                user_id=user_id,
                action="PAYMENT_COMPLETED",
                resource_type="transaction",
                resource_id=txn.id,
                details={
                    "payment_id": payment_id,
                    "amount": amount_value,
                    "old_balance": user.balance if user else None,
                },
            )

        elif payment_status in ("canceled", "refunded"):
            if txn.status not in ("canceled", "refunded"):
                txn.status = payment_status
                logger.info(f"🔄 Transaction marked as {payment_status}")

        await db.commit()
        logger.info(f"✅ Webhook processed successfully: payment_id={payment_id}")
        return {"status": "ok", "payment_id": payment_id}

    except Exception as e:
        import traceback

        logger.error(f"❌ Webhook handler error: {type(e).__name__}: {str(e)}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        await db.rollback()
        return {"status": "error", "detail": str(e)}


@router.post("/topup/manual")
async def manual_topup(
    user_id: str,
    amount: float,
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Manual top-up (admin only)."""
    if current_user.get("role") not in ("admin", "security_auditor"):
        raise HTTPException(status_code=403, detail="Admin access required")

    amount = round(amount, 2)

    # Find target user
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Credit balance
    user.balance += amount

    # Create transaction record
    txn = Transaction(
        user_id=uuid.UUID(user_id),
        amount=amount,
        currency="RUB",
        type="admin_adjustment",
        status="completed",
        payment_method="manual",
        description=description
        or f"Пополнение баланса администратором: {current_user.get('email')}",
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
