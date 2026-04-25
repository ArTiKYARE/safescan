"""
Migration script: Fix domains with NULL verification_method.
Sets verification_method to 'api_token' for domains where it's NULL.
"""

import asyncio
from sqlalchemy import select, update, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Build DATABASE_URL from env or use default
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://safescan:safescan@localhost:5432/safescan"
)


async def migrate():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        # Count affected domains
        result = await conn.execute(
            text("SELECT COUNT(*) FROM domains WHERE verification_method IS NULL")
        )
        count = result.scalar()
        print(f"Found {count} domains with NULL verification_method")

        if count > 0:
            # Update all NULL verification_method to 'api_token'
            result = await conn.execute(
                text(
                    "UPDATE domains SET verification_method = 'api_token' "
                    "WHERE verification_method IS NULL"
                )
            )
            print(f"Updated {result.rowcount} domains to verification_method='api_token'")
        else:
            print("No domains to migrate")

    await engine.dispose()
    print("Migration complete!")


if __name__ == "__main__":
    asyncio.run(migrate())

