"""
SafeScan — Seed Admin User
Run this to promote the first registered user to admin role.

Usage (inside backend container):
    python -m app.scripts.seed_admin
"""

import asyncio
import sys

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User


async def seed_admin():
    """Promote the first user to admin role."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).order_by(User.created_at))
        users = result.scalars().all()

        if not users:
            print("❌ No users found. Register a user first.")
            sys.exit(1)

        first_user = users[0]
        old_role = first_user.role
        first_user.role = "admin"
        await db.commit()

        print(f"✅ User '{first_user.email}' promoted from '{old_role}' → 'admin'")
        print(f"   This user can now scan any domain without verification.")


if __name__ == "__main__":
    asyncio.run(seed_admin())
