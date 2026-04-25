"""Reset admin password"""
from app.core.security import hash_password, verify_password
from app.core.database import engine
from sqlalchemy import text
import asyncio

async def main():
    new_hash = hash_password('admin123')
    import sys
    sys.stderr.write(f"Generated hash: {new_hash[:30]}...\n")
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE users SET password_hash = :h, role = 'admin', email_verified = true WHERE email = 'test@test.com'"),
            {"h": new_hash}
        )
    sys.stderr.write("Password updated!\n")
    
    # Verify
    result = await conn.execute(text("SELECT password_hash FROM users WHERE email = 'test@test.com'"))
    row = result.first()
    if row:
        works = verify_password('admin123', row[0])
        sys.stderr.write(f"Verification test: {'OK' if works else 'FAILED'}\n")
    await engine.dispose()

asyncio.run(main())
