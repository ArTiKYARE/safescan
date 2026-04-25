"""
SafeScan — Vulnerability Scanner Orchestrator

This module orchestrates the execution of all scanning modules against
a target domain. Modules run **in parallel** using asyncio.gather()
for maximum speed, with thread-safe aggregation of results.

Performance optimisations:
- Shared httpx.AsyncClient with connection pooling (no per-request overhead)
- Global asyncio.Semaphore rate limiter (all modules share the same budget)
"""

import asyncio
import logging
import uuid
from typing import Optional
from datetime import datetime, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity
from app.workers.scan_logger import ScanLogger
from app.core.config import settings

logger = logging.getLogger(__name__)


class VulnerabilityScanner:
    """
    Main scanner orchestrator.

    Executes individual scanning modules **in parallel** using asyncio.gather()
    and aggregates results with async locking for thread-safety.

    All modules share a single httpx.AsyncClient for connection pooling
    and a global rate limiter (Semaphore) to avoid overwhelming the target.
    """

    def __init__(
        self,
        scan_id: str,
        domain: str,
        modules: list[str],
        db: AsyncSession,
    ):
        self.scan_id = scan_id
        self.domain = domain
        self.modules = modules
        self.db = db
        self.results: list[ScanResult] = []
        self.findings: list[Finding] = []
        self.scan_logger = ScanLogger(scan_id)
        self._lock = asyncio.Lock()
        self._completed_count = 0
        self._total_modules = len(self.modules)

        # Shared HTTP client with connection pooling
        self._http_client: Optional[httpx.AsyncClient] = None

        # Global rate limiter — semaphore shared across ALL parallel modules
        # Ensures total requests/sec stays within config.SCAN_REQUESTS_PER_SECOND
        rate_limit = (
            settings.SCAN_REQUESTS_PER_SECOND
            if settings.SCAN_REQUESTS_PER_SECOND > 0
            else 10
        )
        self._rate_limiter = asyncio.Semaphore(rate_limit)

        # Separate engine/session for progress updates (committed immediately)
        # Initialize synchronously in __init__ to avoid race conditions
        try:
            from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
            from app.core.config import settings as app_settings

            self._progress_engine = create_async_engine(
                app_settings.DATABASE_URL,
                pool_size=1,
                max_overflow=0,
                pool_pre_ping=True,
            )
            self._progress_session_factory = async_sessionmaker(
                self._progress_engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            self.scan_logger.log("Progress session initialized", "DEBUG")
        except Exception as e:
            logger.error(f"Failed to initialize progress session: {e}")
            self._progress_engine = None
            self._progress_session_factory = None

        try:
            self.scan_logger.log(f"Scanner initialized for {self.domain}", "INFO")
        except Exception as e:
            logger.error(f"ScanLogger init failed: {e}")

    async def _update_progress(self, current_module: str, progress: int):
        """Update scan progress in the database and commit immediately."""
        if self._progress_session_factory is None:
            logger.error(f"Progress session not initialized - cannot update progress")
            return

        try:
            from app.models.scan import Scan
            from sqlalchemy import select, update

            async with self._progress_session_factory() as progress_db:
                result = await progress_db.execute(
                    select(Scan).where(Scan.id == uuid.UUID(self.scan_id))
                )
                scan = result.scalar_one_or_none()
                if scan:
                    scan.current_module = current_module
                    scan.progress_percentage = progress
                    await progress_db.commit()
                    logger.debug(f"Progress updated: {progress}% - {current_module}")
                else:
                    logger.error(f"Scan {self.scan_id} not found in database")
        except Exception as e:
            logger.error(f"Failed to update progress: {e}", exc_info=True)

    async def _update_progress_counts(self, pages_crawled: int, requests_made: int):
        """Update request/page counts in the database."""
        if self._progress_session_factory is None:
            return

        try:
            from app.models.scan import Scan
            from sqlalchemy import select

            async with self._progress_session_factory() as progress_db:
                result = await progress_db.execute(
                    select(Scan).where(Scan.id == uuid.UUID(self.scan_id))
                )
                scan = result.scalar_one_or_none()
                if scan:
                    scan.pages_crawled = max(scan.pages_crawled, pages_crawled)
                    scan.requests_made = max(scan.requests_made, requests_made)
                    await progress_db.commit()
        except Exception as e:
            logger.debug(f"Failed to update counts: {e}")

    async def run(self) -> dict:
        """Execute all scanning modules **in parallel** and return aggregated results."""
        self.scan_logger.log(f"Starting **parallel** scan of {self.domain}", "INFO")
        self.scan_logger.log(
            f"Modules ({self._total_modules}): {', '.join(self.modules)}", "INFO"
        )

        # Set initial progress
        await self._update_progress(current_module="Инициализация", progress=5)

        # Create shared HTTP client with connection pooling
        self._http_client = httpx.AsyncClient(
            verify=True,
            timeout=httpx.Timeout(10.0, connect=5.0),
            follow_redirects=True,
            max_redirects=3,
            limits=httpx.Limits(
                max_connections=20,
                max_keepalive_connections=10,
                keepalive_expiry=30.0,
            ),
        )

        # Import all modules
        from app.workers.modules.security_headers import SecurityHeadersModule
        from app.workers.modules.ssl_tls import SSLTLSModule
        from app.workers.modules.xss import XSSModule
        from app.workers.modules.injection import InjectionModule
        from app.workers.modules.csrf_cors import CSRFCORSModule
        from app.workers.modules.ssrf_xxe_traversal import SSRFXXETraversalModule
        from app.workers.modules.auth_sessions import AuthSessionsModule
        from app.workers.modules.server_config import ServerConfigModule
        from app.workers.modules.sca import SCAModule
        from app.workers.modules.info_leakage import InfoLeakageModule
        from app.workers.modules.app_logic import AppLogicModule
        from app.workers.modules.network import NetworkModule

        # Map module names to classes
        module_registry = {
            "security_headers": SecurityHeadersModule,
            "ssl_tls": SSLTLSModule,
            "xss": XSSModule,
            "injection": InjectionModule,
            "csrf_cors": CSRFCORSModule,
            "ssrf_xxe_traversal": SSRFXXETraversalModule,
            "auth_sessions": AuthSessionsModule,
            "server_config": ServerConfigModule,
            "sca": SCAModule,
            "info_leakage": InfoLeakageModule,
            "app_logic": AppLogicModule,
            "network": NetworkModule,
        }

        # Filter valid modules
        valid_modules = [m for m in self.modules if m in module_registry]
        invalid_modules = [m for m in self.modules if m not in module_registry]

        for module_name in invalid_modules:
            logger.warning(f"Unknown module: {module_name}, skipping")
            self.scan_logger.log(f"Unknown module: {module_name}, skipping", "WARNING")

        if not valid_modules:
            self.scan_logger.log("No valid modules to run", "ERROR")
            await self._http_client.aclose()
            return {
                "total_findings": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "risk_score": 0.0,
                "grade": "A+",
                "modules_run": 0,
                "modules_failed": 0,
            }

        # Launch ALL modules in parallel
        self.scan_logger.log(
            f"Launching {len(valid_modules)} modules in **parallel**...",
            "INFO",
        )

        tasks = [
            self._run_single_module(module_name, module_registry[module_name])
            for module_name in valid_modules
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        # All modules done
        progress = 90
        await self._update_progress(
            current_module="Сохранение результатов", progress=progress
        )

        # Close shared HTTP client
        if self._http_client:
            await self._http_client.aclose()

        # All modules completed — save remaining findings
        async with self._lock:
            await self._save_findings(self.findings)

        # Calculate overall risk score and grade
        risk_score = self._calculate_risk_score()
        grade = self._calculate_grade(risk_score)

        # Set progress to 100
        await self._update_progress(current_module="Завершено", progress=100)

        self.scan_logger.log(
            f"Scan completed: {len(self.findings)} total findings, risk score {risk_score}, grade {grade}",
            "INFO",
        )

        return {
            "total_findings": len(self.findings),
            "critical": sum(
                1 for f in self.findings if f.severity == Severity.CRITICAL
            ),
            "high": sum(1 for f in self.findings if f.severity == Severity.HIGH),
            "medium": sum(1 for f in self.findings if f.severity == Severity.MEDIUM),
            "low": sum(1 for f in self.findings if f.severity == Severity.LOW),
            "info": sum(1 for f in self.findings if f.severity == Severity.INFO),
            "risk_score": risk_score,
            "grade": grade,
            "modules_run": len(self.results),
            "modules_failed": sum(1 for r in self.results if not r.success),
        }

    async def _run_single_module(self, module_name: str, module_class):
        """Execute a single module and handle its results (called in parallel)."""
        module = module_class(
            domain=self.domain,
            scan_id=self.scan_id,
            config=settings,
            client=self._http_client,
            rate_limiter=self._rate_limiter,
        )

        try:
            self.scan_logger.log(
                f"Starting module {self._completed_count + 1}/{self._total_modules}: {module_name}",
                "INFO",
                module_name,
            )
            result = await module.execute()

            async with self._lock:
                self.results.append(result)
                self.findings.extend(result.findings)
                self._completed_count += 1
                completed = self._completed_count

                severity_counts = {}
                for f in result.findings:
                    sev = f.severity.value
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1

                summary = (
                    ", ".join(f"{k}: {v}" for k, v in severity_counts.items())
                    if severity_counts
                    else "no findings"
                )
                self.scan_logger.log(
                    f"Module {module_name} completed: {len(result.findings)} findings ({summary})",
                    (
                        "INFO"
                        if not any(
                            f.severity in (Severity.CRITICAL, Severity.HIGH)
                            for f in result.findings
                        )
                        else "WARN"
                    ),
                    module_name,
                )

                # Log individual findings
                for f in result.findings:
                    if f.severity in (
                        Severity.CRITICAL,
                        Severity.HIGH,
                        Severity.MEDIUM,
                    ):
                        self.scan_logger.log(
                            f"[{f.severity.value.upper()}] {f.title}",
                            "WARN" if f.severity != Severity.CRITICAL else "ERROR",
                            module_name,
                        )

                # Update progress: 10-90 range for modules
                progress = min(90, 10 + int((completed / self._total_modules) * 80))
                await self._update_progress(
                    current_module=module_name,
                    progress=progress,
                )

                # Update request/page counts
                total_requests = sum(r.requests_made for r in self.results)
                total_pages = sum(r.pages_crawled for r in self.results)
                await self._update_progress_counts(total_pages, total_requests)

        except Exception as e:
            logger.error(f"Module {module_name} failed: {e}", exc_info=True)
            self.scan_logger.log(
                f"Module {module_name} failed: {str(e)[:200]}",
                "ERROR",
                module_name,
            )
            async with self._lock:
                self.results.append(
                    ScanResult(
                        module=module_name,
                        success=False,
                        error=str(e),
                        findings=[],
                    )
                )
                self._completed_count += 1
                completed = self._completed_count

            # Update progress even for failed modules
            progress = min(90, 10 + int((completed / self._total_modules) * 80))
            await self._update_progress(
                current_module=module_name,
                progress=progress,
            )

    async def _save_findings(self, findings: list[Finding]):
        """Save findings to the database."""
        import uuid
        from app.models.vulnerability import Vulnerability

        for finding in findings:
            vuln = Vulnerability(
                scan_id=uuid.UUID(self.scan_id),
                module=finding.module,
                title=finding.title,
                description=finding.description,
                severity=finding.severity.value,
                cvss_score=finding.cvss_score,
                cvss_vector=finding.cvss_vector,
                affected_url=finding.affected_url,
                affected_parameter=finding.affected_parameter,
                evidence=finding.evidence,
                remediation=finding.remediation,
                cwe_id=finding.cwe_id,
                cwe_name=finding.cwe_name,
                owasp_category=finding.owasp_category,
                owasp_name=finding.owasp_name,
            )
            self.db.add(vuln)

        await self.db.flush()

    def _calculate_risk_score(self) -> float:
        """
        Calculate overall risk score (0-10).

        Weighted formula:
        - Critical: 10.0 each
        - High: 7.5 each
        - Medium: 4.0 each
        - Low: 1.0 each
        - Info: 0.0 each

        Normalized to 0-10 scale with diminishing returns.
        """
        weights = {
            Severity.CRITICAL: 10.0,
            Severity.HIGH: 7.5,
            Severity.MEDIUM: 4.0,
            Severity.LOW: 1.0,
            Severity.INFO: 0.0,
        }

        total_weight = sum(weights[f.severity] for f in self.findings)

        # Normalize to 0-10 with logarithmic scaling
        import math

        if total_weight == 0:
            return 0.0

        risk_score = min(10.0, math.log10(total_weight + 1) * 3.5)
        return round(risk_score, 1)

    def _calculate_grade(self, risk_score: float) -> str:
        """Calculate letter grade based on risk score."""
        if risk_score == 0:
            return "A+"
        elif risk_score < 1.5:
            return "A"
        elif risk_score < 3.0:
            return "B"
        elif risk_score < 5.0:
            return "C"
        elif risk_score < 7.0:
            return "D"
        else:
            return "F"
