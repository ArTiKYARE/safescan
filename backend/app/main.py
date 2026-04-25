"""
SafeScan — Legal Web Vulnerability Scanning Platform
Main Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.security import setup_security
from app.api.v1.router import api_router as v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Database tables are managed via Alembic migrations.
    # Run 'alembic upgrade head' to apply migrations.
    # In development mode, create tables if they don't exist as fallback.
    if settings.APP_ENV == "development":
        from app.core.database import engine, Base
        import app.models  # noqa: F401 — register all models with Base.metadata

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # MinIO bucket initialization
    try:
        await _ensure_bucket()
    except Exception:
        pass

    print(f"🚀 SafeScan started in {settings.APP_ENV} mode")
    yield
    # Shutdown
    from app.workers.scan_logger import _RedisPool

    _RedisPool.close()
    from app.core.database import engine

    await engine.dispose()
    print("👋 SafeScan shut down")


async def _ensure_bucket():
    """Ensure S3/MinIO bucket exists."""
    import aioboto3

    session = aioboto3.Session()
    async with session.client(
        "s3",
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    ) as client:
        try:
            await client.create_bucket(Bucket=settings.S3_BUCKET)
            print(f"✅ Created bucket: {settings.S3_BUCKET}")
        except client.exceptions.BucketAlreadyOwnedByYou:
            pass
        except Exception:
            pass


def create_application() -> FastAPI:
    """Create and configure FastAPI application."""

    app = FastAPI(
        title=settings.APP_NAME,
        description="Legal Web Vulnerability Scanning Platform — Detection, not exploitation.",
        version="1.0.0",
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
        openapi_url="/openapi.json" if settings.APP_DEBUG else None,
        lifespan=lifespan,
    )

    # CORS — MUST be added FIRST (last in LIFO order) to handle all requests including errors
    origins = (
        settings.APP_CORS_ORIGINS.split(",")
        if settings.APP_CORS_ORIGINS
        else ["http://localhost:3000"]
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Security middleware (added after CORS so it runs inside CORS wrapper)
    setup_security(app)

    # Root endpoint
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "name": settings.APP_NAME,
            "version": "1.0.0",
            "status": "running",
            "environment": settings.APP_ENV,
        }

    @app.get("/health", tags=["Health"])
    async def health_check():
        return {
            "status": "healthy",
            "service": "safescan-api",
        }

    # Include API router
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_application()
