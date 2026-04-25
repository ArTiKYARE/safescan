"""
SafeScan — SSRF, XXE, Path Traversal Module

Detects Server-Side Request Forgery, XML External Entity,
and Path Traversal vulnerabilities.

All payloads are SAFE detection-only.
Standards: OWASP-A10:2021, ASVS-V8, CWE-918, CWE-611, CWE-22
"""

import asyncio
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class SSRFXXETraversalModule(ScanModule):
    """Module for SSRF, XXE, and Path Traversal detection."""

    # SSRF detection payloads (safe)
    SSRF_PAYLOADS = [
        "http://169.254.169.254/latest/meta-data/",  # AWS metadata
        "http://127.0.0.1/",
        "http://localhost/",
        "file:///etc/passwd",
    ]

    # XXE payloads (safe detection)
    XXE_PAYLOADS = [
        '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY xxe "SXSCANX">]><root>&xxe;</root>',
    ]

    # Path traversal payloads
    TRAVERSAL_PAYLOADS = [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
    ]

    async def execute(self) -> ScanResult:
        """Execute SSRF/XXE/Traversal detection."""
        self.start_time = asyncio.get_event_loop().time()

        input_points = await self._discover_input_points()

        # Test SSRF
        for point in input_points:
            await self._test_ssrf(point)

        # Test XXE on XML endpoints
        await self._test_xxe()

        # Test Path Traversal
        for point in input_points:
            await self._test_path_traversal(point)

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="ssrf_xxe_traversal",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _discover_input_points(self) -> list[dict]:
        """Discover potential SSRF/Traversal injection points."""
        points = []
        response = await self._make_request(path="/")

        if response and response.text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            seen = set()
            for form in soup.find_all("form"):
                for inp in form.find_all(["input", "textarea"]):
                    name = inp.get("name")
                    if name and name not in seen:
                        seen.add(name)
                        points.append({
                            "url": form.get("action", "/"),
                            "method": form.get("method", "get").lower(),
                            "parameter": name,
                        })

        # Common parameters that might be SSRF-vulnerable
        for param in ["url", "link", "redirect", "image", "src", "path", "file"]:
            if param not in points:
                points.append({
                    "url": "/",
                    "method": "get",
                    "parameter": param,
                })

        return points[:10]  # Reduced from 15 to 10 for speed

    async def _test_ssrf(self, point: dict):
        """Test for SSRF vulnerability."""
        for payload in self.SSRF_PAYLOADS:
            if point["method"] == "get":
                response = await self._make_request(
                    path=point["url"],
                    params={point["parameter"]: payload},
                    timeout=3.0,  # Short timeout for SSRF
                )
            else:
                response = await self._make_request(
                    path=point["url"],
                    method="POST",
                    data={point["parameter"]: payload},
                    timeout=3.0,
                )

            if response:
                # Check for internal IP responses or metadata
                if any(kw in response.text.lower() for kw in ["ami-id", "instance-id", "root:x:"]):
                    self._log_finding(self._create_finding(
                        title=f"SSRF в параметре '{point['parameter']}'",
                        description=(
                            f"Параметр '{point['parameter']}' выполняет серверные запросы "
                            f"к внутренним ресурсам. Обнаружены метаданные инфраструктуры или системные файлы."
                        ),
                        severity=Severity.CRITICAL,
                        remediation=(
                            "Валидируйте и добавляйте разрешённые URL на стороне сервера. "
                            "Блокируйте запросы к частным IP-диапазонам. "
                            "Отключите неиспользуемые URL-протоколы (file://, gopher://, ftp://)."
                        ),
                        cvss_score=9.1,
                        cwe_id="CWE-918",
                        owasp_category="A10:2021",
                        owasp_name="SSRF",
                        affected_url=str(response.url),
                        affected_parameter=point["parameter"],
                        evidence="Обнаружено содержимое внутреннего ресурса",
                    ))
                    return

    async def _test_xxe(self):
        """Test for XXE on XML endpoints."""
        xml_endpoints = ["/api/xml", "/api/soap", "/rpc", "/xml"]

        for endpoint in xml_endpoints:
            for payload in self.XXE_PAYLOADS:
                response = await self._make_request(
                    path=endpoint,
                    method="POST",
                    data=payload,
                    headers={"Content-Type": "application/xml"},
                )

                if response and "SXSCANX" in response.text:
                    self._log_finding(self._create_finding(
                        title=f"Внешняя сущность XML (XXE) на {endpoint}",
                        description=(
                            f"XML-эндпоинт {endpoint} обрабатывает внешние сущности."
                        ),
                        severity=Severity.CRITICAL,
                        remediation=(
                            "Отключите обработку DTD/внешних сущностей в XML-парсере."
                        ),
                        cvss_score=9.0,
                        cwe_id="CWE-611",
                        owasp_category="A05:2021",
                        affected_url=f"{self.base_url}{endpoint}",
                        evidence="XXE-сущность обработана: SXSCANX",
                    ))
                    return

    async def _test_path_traversal(self, point: dict):
        """Test for Path Traversal vulnerability."""
        for payload in self.TRAVERSAL_PAYLOADS:
            response = await self._make_request(
                path=point["url"],
                params={point["parameter"]: payload},
            )

            if response and response.text:
                # Check for /etc/passwd content
                if "root:x:" in response.text or "root:*:" in response.text:
                    self._log_finding(self._create_finding(
                        title=f'Обход путей (Path Traversal) в параметре "{point["parameter"]}"',
                        description=(
                            f'Параметр "{point["parameter"]}" позволяет обход каталогов, '
                            f"позволяя читать произвольные файлы с сервера."
                        ),
                        severity=Severity.HIGH,
                        remediation=(
                            "Валидируйте пути к файлам по белому списку. "
                            "Используйте chroot/jail для файловых операций."
                        ),
                        cvss_score=7.5,
                        cwe_id="CWE-22",
                        owasp_category="A01:2021",
                        affected_url=str(response.url),
                        affected_parameter=point["parameter"],
                        evidence="Обнаружено содержимое системного файла",
                    ))
                    return
