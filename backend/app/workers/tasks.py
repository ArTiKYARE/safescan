"""
SafeScan — Celery Task Definitions
"""

import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional

from celery.exceptions import SoftTimeLimitExceeded
from app.workers.celery_app import celery_app
from app.core.config import settings
from app.core.database import (
    AsyncSessionLocal,
    engine,
    AsyncSessionLocal as SessionFactory,
)
from app.workers.scanner import VulnerabilityScanner
from app.services.audit import log_audit_event

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine in a fresh event loop (safe for Celery prefork workers)."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    name="app.workers.tasks.run_scan",
    bind=True,
    max_retries=2,
    soft_time_limit=600,  # 10 minutes for parallel scans
    time_limit=720,  # 12 minutes hard limit
)
def run_scan(self, scan_id: str, domain: str, modules: list[str]):
    """Execute a vulnerability scan."""
    logger.info(
        f"Starting scan task: scan_id={scan_id}, domain={domain}, modules={modules}"
    )

    async def _run():
        # Create a fresh engine + session for this task
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from app.core.database import Base
        from app.core.config import settings as app_settings

        task_engine = create_async_engine(
            app_settings.DATABASE_URL,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
        )
        task_session_factory = async_sessionmaker(
            task_engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        async with task_session_factory() as db:
            try:
                from app.models.scan import Scan
                from sqlalchemy import select

                # Get scan record
                result = await db.execute(
                    select(Scan).where(Scan.id == uuid.UUID(scan_id))
                )
                scan = result.scalar_one_or_none()
                if not scan:
                    logger.error(f"Scan {scan_id} not found in database")
                    await task_engine.dispose()
                    return {"error": "Scan not found"}

                logger.info(f"Scan record found: status={scan.status}")
                scan.status = "running"
                scan.started_at = datetime.now(timezone.utc)
                await db.commit()

                # Run scanner
                logger.info(f"Initializing VulnerabilityScanner for {domain}")
                scanner = VulnerabilityScanner(
                    scan_id=scan_id,
                    domain=domain,
                    modules=modules,
                    db=db,
                )
                logger.info(f"Starting scanner.run()")
                results = await scanner.run()
                logger.info(f"Scanner completed: {results}")

                # Save reports to S3
                from app.services.report_generator import ReportGeneratorService

                report_gen = ReportGeneratorService(db)
                s3_keys = await report_gen.save_reports_to_s3(scan)

                # Update scan with results
                scan.status = "completed"
                scan.completed_at = datetime.now(timezone.utc)
                scan.current_module = "Завершено"
                scan.progress_percentage = 100
                scan.total_findings = results["total_findings"]
                scan.critical_count = results["critical"]
                scan.high_count = results["high"]
                scan.medium_count = results["medium"]
                scan.low_count = results["low"]
                scan.info_count = results["info"]
                scan.risk_score = results["risk_score"]
                scan.grade = results["grade"]
                await db.commit()

                await task_engine.dispose()

                return {
                    "scan_id": scan_id,
                    "status": "completed",
                    "findings": results["total_findings"],
                }

            except Exception as e:
                # Handle scan failure with proper retry logic
                error_msg = str(e)[:500]

                # Check if we've exhausted retries
                current_retries = self.request.retries or 0
                max_retries = self.max_retries or 2

                if current_retries < max_retries:
                    # Will retry — don't mark as failed yet, just log
                    logger.warning(
                        f"Scan {scan_id} failed (attempt {current_retries + 1}/{max_retries + 1}), "
                        f"retrying in 60s: {e}"
                    )
                else:
                    # Final retry — mark as failed permanently
                    logger.error(
                        f"Scan {scan_id} failed permanently after {max_retries} retries: {e}",
                        exc_info=True,
                    )
                    try:
                        from app.models.scan import Scan
                        from sqlalchemy import select

                        result = await db.execute(
                            select(Scan).where(Scan.id == uuid.UUID(scan_id))
                        )
                        scan = result.scalar_one_or_none()
                        if scan:
                            scan.status = "failed"
                            scan.error_message = error_msg
                            scan.completed_at = datetime.now(timezone.utc)
                            await db.commit()
                    except Exception as db_err:
                        logger.error(f"Failed to update scan status: {db_err}")

                try:
                    await task_engine.dispose()
                except Exception:
                    pass

                # Retry logic
                raise self.retry(exc=e, countdown=60)

            except SoftTimeLimitExceeded:
                # Handle Celery soft timeout — mark as failed immediately
                error_msg = (
                    f"Scan timed out after {self.request.get('soft_time_limit', 600)}s"
                )
                logger.error(f"Scan {scan_id} timed out: {error_msg}")
                try:
                    from app.models.scan import Scan
                    from sqlalchemy import select

                    result = await db.execute(
                        select(Scan).where(Scan.id == uuid.UUID(scan_id))
                    )
                    scan = result.scalar_one_or_none()
                    if scan:
                        scan.status = "failed"
                        scan.error_message = error_msg
                        scan.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                except Exception as db_err:
                    logger.error(f"Failed to update scan status on timeout: {db_err}")

                try:
                    await task_engine.dispose()
                except Exception:
                    pass

                raise

    return _run_async(_run())


@celery_app.task(name="app.workers.tasks.verify_domain")
def verify_domain(domain_id: str):
    """Verify domain ownership."""

    async def _verify():
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from app.models.domain import Domain
        from sqlalchemy import select

        task_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=1,
            max_overflow=0,
        )
        task_session_factory = async_sessionmaker(task_engine, expire_on_commit=False)

        async with task_session_factory() as db:
            result = await db.execute(
                select(Domain).where(Domain.id == uuid.UUID(domain_id))
            )
            domain = result.scalar_one_or_none()
            if not domain:
                await task_engine.dispose()
                return {"error": "Domain not found"}

            # Simple verification — just check domain resolves
            import socket

            try:
                socket.gethostbyname(domain.domain)
                domain.is_verified = True
                domain.verified_at = datetime.now(timezone.utc)
                await db.commit()
                verified = True
            except Exception:
                verified = False

            await task_engine.dispose()
            return {"domain_id": domain_id, "verified": verified}

    return _run_async(_verify())


@celery_app.task(name="app.workers.tasks.cleanup_old_data")
def cleanup_old_data():
    """Periodic cleanup of old data based on retention policy."""

    async def _cleanup():
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from app.models.scan import Scan
        from app.models.audit_log import AuditLog
        from sqlalchemy import select

        task_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=1,
            max_overflow=0,
        )
        task_session_factory = async_sessionmaker(task_engine, expire_on_commit=False)

        cutoff_date = datetime.now(timezone.utc) - timedelta(
            days=settings.DATA_RETENTION_DAYS
        )

        async with task_session_factory() as db:
            result = await db.execute(
                select(Scan).where(
                    Scan.status == "completed",
                    Scan.completed_at < cutoff_date,
                )
            )
            old_scans = result.scalars().all()
            count = len(old_scans)
            for scan in old_scans:
                await db.delete(scan)

            await db.commit()
            await task_engine.dispose()
            return {"cleaned_scans": count}

    return _run_async(_cleanup())


@celery_app.task(name="app.workers.tasks.reverify_domains")
def reverify_domains():
    """Periodic re-verification of domains."""

    async def _reverify():
        from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
        from app.models.domain import Domain
        from sqlalchemy import select
        import socket

        task_engine = create_async_engine(
            settings.DATABASE_URL,
            pool_size=1,
            max_overflow=0,
        )
        task_session_factory = async_sessionmaker(task_engine, expire_on_commit=False)

        async with task_session_factory() as db:
            result = await db.execute(select(Domain).where(Domain.is_verified == True))
            domains = result.scalars().all()

            verified_count = 0
            for domain in domains:
                try:
                    socket.gethostbyname(domain.domain)
                    domain.last_reverification = datetime.now(timezone.utc)
                    verified_count += 1
                except Exception:
                    domain.is_verified = False

            await db.commit()
            await task_engine.dispose()
            return {"total": len(domains), "verified": verified_count}

    return _run_async(_reverify())
