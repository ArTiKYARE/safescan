"""
SafeScan — Server Configuration Module

Checks directory listing, debug endpoints, software versions,
HTTP methods, error page information disclosure.

Standards: ASVS-V8, CIS Benchmark
"""

import asyncio
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class ServerConfigModule(ScanModule):
    """Module for server configuration checks."""

    # Known debug/development endpoints
    DEBUG_ENDPOINTS = [
        "/debug",
        "/debug/vars",
        "/debug/pprof",
        "/actuator",
        "/actuator/env",
        "/actuator/beans",
        "/actuator/health",
        "/actuator/metrics",
        "/phpinfo.php",
        "/info.php",
        "/phpinfo",
        "/console",
        "/admin",
        "/admin/debug",
        "/admin/config",
        "/graphql",
        "/graphiql",
        "/swagger",
        "/swagger-ui",
        "/swagger-ui.html",
        "/api-docs",
        "/api/docs",
        "/redoc",
        "/docs",
        "/api/swagger",
        "/trace",
        "/heapdump",
        "/env",
        "/config",
        "/.well-known/security.txt",
    ]

    async def execute(self) -> ScanResult:
        """Execute server configuration checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_directory_listing()
        await self._check_debug_endpoints()
        await self._check_http_methods()
        await self._check_error_pages()
        await self._check_technology_headers()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="server_config",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_directory_listing(self):
        """Check for directory listing enabled."""
        dirs_to_check = ["/", "/static/", "/assets/", "/css/", "/js/", "/images/", "/uploads/"]

        for directory in dirs_to_check:
            response = await self._make_request(path=directory)
            if response and response.status_code == 200:
                # Check for directory listing indicators
                is_listing = False
                indicators = [
                    "index of",
                    "<title>index of",
                    "directory listing for",
                    "last modified</a>",
                    "parent directory",
                ]

                for indicator in indicators:
                    if indicator in response.text.lower():
                        is_listing = True
                        break

                if is_listing:
                    self._log_finding(self._create_finding(
                        title=f"Включён листинг директории: {directory}",
                        description=(
                            f"Листинг директории включён по пути {directory}, "
                            f"что раскрывает структуру файлов и потенциально конфиденциальные файлы."
                        ),
                        severity=Severity.MEDIUM,
                        remediation=(
                            "Отключите листинг директорий в конфигурации веб-сервера.\n"
                            "- Apache: Options -Indexes\n"
                            "- Nginx: autoindex off;\n"
                            "- IIS: отключите Directory Browsing"
                        ),
                        cvss_score=5.3,
                        cwe_id="CWE-548",
                        owasp_category="A05:2021",
                        affected_url=f"{self.base_url}{directory}",
                        evidence="Обнаружена страница листинга директории",
                    ))

    async def _check_debug_endpoints(self):
        """Scan for debug/development endpoints."""
        # Process endpoints in parallel batches of 10
        batch_size = 10
        
        for i in range(0, len(self.DEBUG_ENDPOINTS), batch_size):
            batch = self.DEBUG_ENDPOINTS[i:i + batch_size]
            tasks = [self._check_single_endpoint(ep) for ep in batch]
            await asyncio.gather(*tasks)

    async def _check_single_endpoint(self, endpoint: str):
        """Check a single debug endpoint."""
        # Skip security.txt — it's good
        if endpoint == "/.well-known/security.txt":
            return

        response = await self._make_request(path=endpoint)

        if response and response.status_code == 200:
            # Check for debug content indicators
            debug_indicators = ["phpinfo()", "debug_toolbar", "swagger", "graphiql", "actuator", "environment variables"]

            is_debug = any(ind in response.text.lower() for ind in debug_indicators)

            if is_debug or endpoint in ["/phpinfo.php", "/info.php", "/console"]:
                severity = Severity.HIGH if "phpinfo" in endpoint or "console" in endpoint else Severity.MEDIUM

                self._log_finding(self._create_finding(
                    title=f"Доступна отладочная эндпоинт: {endpoint}",
                    description=(
                        f"Отладочная/разработческая эндпоинт доступна по адресу {endpoint}. "
                        f"Это может раскрывать конфиденциальную информацию о конфигурации."
                    ),
                    severity=severity,
                    remediation=(
                        "Удалите или ограничьте доступ к отладочным эндпоинтам в production. "
                        "Используйте правила файрвола или аутентификацию для ограничения доступа. "
                        "Отключите режим отладки в конфигурации приложения."
                    ),
                    cvss_score=6.5 if severity == Severity.HIGH else 4.3,
                    cwe_id="CWE-215",
                    owasp_category="A05:2021",
                    affected_url=f"{self.base_url}{endpoint}",
                    evidence="Эндпоинт вернул 200 OK",
                ))

    async def _check_http_methods(self):
        """Check for dangerous HTTP methods."""
        # Check for TRACE method (XST attack)
        response = await self._make_request(method="TRACE", path="/")
        if response and response.status_code == 200:
            self._log_finding(self._create_finding(
                title="Включён HTTP-метод TRACE",
                description=(
                    "Метод TRACE включён, что может быть использовано для "
                    "атак Cross-Site Tracing (XST) с целью кражи учётных данных."
                ),
                severity=Severity.MEDIUM,
                remediation="Отключите метод TRACE в конфигурации веб-сервера.",
                cvss_score=5.8,
                cwe_id="CWE-693",
                owasp_category="A05:2021",
                evidence="Метод TRACE вернул 200 OK",
            ))

        # Check for OPTIONS method
        response = await self._make_request(method="OPTIONS", path="/")
        if response and response.status_code in (200, 204):
            allow = response.headers.get("allow", "") or response.headers.get("public", "")
            if allow:
                dangerous_methods = ["PUT", "DELETE", "PATCH"]
                for method in dangerous_methods:
                    if method in allow.upper():
                        self._log_finding(self._create_finding(
                            title=f"Разрешён опасный HTTP-метод: {method}",
                            description=(
                                f"Метод {method} разрешён на корневом пути. "
                                f"Убедитесь, что это предусмотрено и защищено."
                            ),
                            severity=Severity.INFO,
                            remediation=f"Ограничьте метод {method} только для аутентифицированных пользователей.",
                            evidence=f"Allow: {allow}",
                        ))

    async def _check_error_pages(self):
        """Check error pages for information disclosure."""
        error_paths = ["/nonexistent-page-12345", "/api/nonexistent-12345"]

        for path in error_paths:
            response = await self._make_request(path=path)
            if response and response.status_code in (404, 500, 403):
                # Check for stack traces or debug info
                disclosure_indicators = [
                    "stack trace",
                    "traceback",
                    "exception",
                    "at line ",
                    "file ",
                    "debug",
                    "at ",
                    "source error",
                    "runtime error",
                    "fatal error",
                    "warning:",
                ]

                for indicator in disclosure_indicators:
                    if indicator.lower() in response.text.lower():
                        self._log_finding(self._create_finding(
                            title="Раскрытие информации на странице ошибок",
                            description=(
                                f"Страница ошибки ({response.status_code}) содержит отладочную информацию "
                                f"или стек-трейсы, которые могут помочь злоумышленникам."
                            ),
                            severity=Severity.MEDIUM,
                            remediation=(
                                "Настройте пользовательские страницы ошибок, которые не раскрывают "
                                "стек-трейсы, пути к файлам или информацию о версиях. "
                                "Установите debug=False в production."
                            ),
                            cvss_score=5.3,
                            cwe_id="CWE-200",
                            owasp_category="A05:2021",
                            evidence=f"Страница ошибки содержит: {indicator}",
                        ))
                        break

    async def _check_technology_headers(self):
        """Check for technology disclosure in headers."""
        response = await self._make_request(path="/")
        if not response:
            return

        disclosure_headers = {
            "server": "Раскрытие версии сервера",
            "x-powered-by": "Раскрытие технологического стека",
            "x-aspnet-version": "Раскрытие версии ASP.NET",
            "x-aspnetmvc-version": "Раскрытие версии ASP.NET MVC",
            "x-generator": "Раскрытие CMS-генератора",
            "x-runtime": "Информация о среде выполнения",
            "x-version": "Раскрытие версии",
        }

        for header, description in disclosure_headers.items():
            value = response.headers.get(header)
            if value:
                self._log_finding(self._create_finding(
                    title=f"Раскрытие информации: {header}",
                    description=f"{description}: {value}",
                    severity=Severity.INFO,
                    remediation=f"Удалите или замаскируйте заголовок {header}.",
                    evidence=f"{header}: {value}",
                ))
