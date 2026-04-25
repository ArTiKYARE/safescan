"""
Create a new admin user for SafeScan.

Usage:
    python create_admin.py
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.security import hash_password
from app.core.database import engine, Base
from sqlalchemy import text
import uuid


async def main():
    # --- Config ---
    email = "admin@safescan.io"
    password = "Admin12345!"
    first_name = "Admin"
    last_name = "SafeScan"
    role = "admin"

    new_hash = hash_password(password)

    async with engine.begin() as conn:
        # Check if user exists
        result = await conn.execute(
            text("SELECT id, role, is_blocked, is_active, email_verified FROM users WHERE email = :email"),
            {"email": email},
        )
        row = result.first()

        if row:
            user_id, current_role, is_blocked, is_active, email_verified = row
            print(f"⚠️  Пользователь {email} уже существует.")
            print(f"   Role: {current_role} | Blocked: {is_blocked} | Active: {is_active} | Verified: {email_verified}")

            # Un-block and ensure admin role
            await conn.execute(
                text("""
                    UPDATE users
                    SET password_hash = :pw,
                        role = :role,
                        is_blocked = false,
                        is_active = true,
                        email_verified = true,
                        failed_login_attempts = 0,
                        locked_until = null
                    WHERE email = :email
                """),
                {"pw": new_hash, "role": role, "email": email},
            )
            print(f"✅ Пароль сброшен на: {password}")
            print(f"✅ Блокировка снята, роль установлена: {role}")
        else:
            # Create new admin user
            user_id = str(uuid.uuid4())
            await conn.execute(
                text("""
                    INSERT INTO users
                    (id, email, password_hash, first_name, last_name, role,
                     email_verified, is_active, is_blocked, mfa_enabled,
                     balance, free_scans_remaining, settings, failed_login_attempts)
                    VALUES
                    (:id, :email, :pw, :fn, :ln, :role,
                     true, true, false, false,
                     0.0, 5, '{}'::jsonb, 0)
                """),
                {
                    "id": user_id,
                    "email": email,
                    "pw": new_hash,
                    "fn": first_name,
                    "ln": last_name,
                    "role": role,
                },
            )
            print(f"✅ Создан новый администратор:")
            print(f"   Email:    {email}")
            print(f"   Пароль:   {password}")
            print(f"   Имя:      {first_name} {last_name}")
            print(f"   Роль:     {role}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
