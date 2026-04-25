"""
SafeScan — Scanning Module Base

All scanning modules inherit from ScanModule and return ScanResult
with a list of Finding objects.
"""

import abc
import asyncio
import logging
from enum import Enum
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


class Severity(str, Enum):
    """Vulnerability severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Finding:
    """A single vulnerability finding."""
    module: str
    title: str
    description: str
    severity: Severity
    remediation: str

    # Optional details
    cvss_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    affected_url: Optional[str] = None
    affected_parameter: Optional[str] = None
    evidence: Optional[str] = None
    cwe_id: Optional[str] = None
    cwe_name: Optional[str] = None
    owasp_category: Optional[str] = None
    owasp_name: Optional[str] = None
    nist_control: Optional[str] = None
    remediation_priority: Optional[str] = None


@dataclass
class ScanResult:
    """Result of a scanning module execution."""
    module: str
    findings: list[Finding]
    success: bool = True
    error: Optional[str] = None
    duration_seconds: float = 0.0
    requests_made: int = 0
    pages_crawled: int = 0


class ScanModule(abc.ABC):
    """
    Base class for all scanning modules.

    Each module must implement execute() which returns a ScanResult.
    Uses a shared httpx.AsyncClient for connection pooling.
    """

    def __init__(self, domain: str, scan_id: str, config,
                 client: Optional[httpx.AsyncClient] = None,
                 rate_limiter: Optional[asyncio.Semaphore] = None):
        self.domain = domain
        self.scan_id = scan_id
        self.config = config
        self.findings: list[Finding] = []
        self.requests_made = 0
        self.start_time: Optional[datetime] = None

        # Build target URLs
        self.scheme = "https"
        self.base_url = f"https://{domain}"
        self.user_agent = config.SCAN_USER_AGENT
        self.timeout = config.SCAN_TIMEOUT_SECONDS
        self.max_crawl_depth = config.SCAN_MAX_CRAWL_DEPTH
        self.max_pages = config.SCAN_MAX_PAGES
        self.rate_limit = config.SCAN_REQUESTS_PER_SECOND

        # Shared client and global rate limiter
        self._client = client
        self._rate_limiter = rate_limiter

    @abc.abstractmethod
    async def execute(self) -> ScanResult:
        """Execute the scanning module and return results."""
        pass

    async def _make_request(
        self,
        method: str = "GET",
        url: Optional[str] = None,
        path: str = "",
        headers: Optional[dict] = None,
        params: Optional[dict] = None,
        data: Optional[dict] = None,
        json_data: Optional[dict] = None,
        follow_redirects: bool = True,
        timeout: Optional[float] = None,
    ) -> Optional[httpx.Response]:
        """
        Make an HTTP request with safe defaults.

        Uses shared client for connection pooling and global rate limiter
        to prevent overwhelming the target server.
        """
        target_url = url or urljoin(self.base_url, path)

        request_headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "identity",
            **(headers or {}),
        }

        # Global rate limiter (shared semaphore across all parallel modules)
        if self._rate_limiter:
            async with self._rate_limiter:
                pass

        try:
            client = self._client or httpx.AsyncClient(
                verify=True,
                timeout=httpx.Timeout(timeout or 10.0, connect=5.0),
                follow_redirects=follow_redirects,
                max_redirects=3,
                limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
            )

            should_close = self._client is None
            response = await client.request(
                method=method,
                url=target_url,
                headers=request_headers,
                params=params,
                data=data,
                json=json_data,
            )
            self.requests_made += 1

            if should_close:
                await client.aclose()

            return response
        except httpx.TimeoutException:
            logger.debug(f"Timeout requesting {target_url}")
            return None
        except httpx.ConnectError:
            logger.debug(f"Connection failed: {target_url}")
            return None
        except Exception as e:
            logger.debug(f"Error requesting {target_url}: {e}")
            return None

    def _create_finding(self, **kwargs) -> Finding:
        """Create a finding with module context."""
        return Finding(module=self.__class__.__name__, **kwargs)

    def _log_finding(self, finding: Finding):
        """Log a finding and add to results."""
        self.findings.append(finding)
        logger.info(
            f"[{finding.severity.value.upper()}] {finding.title}"
        )
