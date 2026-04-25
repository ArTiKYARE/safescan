"""
SafeScan — Security Headers Module

Checks for the presence and correctness of HTTP security headers.
Covers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy,
        Permissions-Policy, COOP, CORP, COEP, Server header removal.

Standards: OWASP-A05:2021, ASVS-V7, NIST-SC-8
"""

import asyncio
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class SecurityHeadersModule(ScanModule):
    """Module for checking HTTP security headers."""

    async def execute(self) -> ScanResult:
        """Execute security headers checks."""
        self.start_time = asyncio.get_event_loop().time()

        # Check main page headers
        response = await self._make_request(path="/")

        if response:
            self._check_hsts(response)
            self._check_csp(response)
            self._check_x_content_type_options(response)
            self._check_xframe_options(response)
            self._check_referrer_policy(response)
            self._check_permissions_policy(response)
            self._check_coop(response)
            self._check_corp(response)
            self._check_coep(response)
            self._check_server_header(response)

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="security_headers",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    def _check_hsts(self, response):
        """Check Strict-Transport-Security header."""
        hsts = response.headers.get("strict-transport-security")

        if not hsts:
            self._log_finding(self._create_finding(
                title="Отсутствует заголовок HSTS",
                description=(
                    "Заголовок Strict-Transport-Security не установлен. "
                    "Этот заголовок указывает браузеру подключаться только через HTTPS, "
                    "предотвращая атаки на понижение версии протокола."
                ),
                severity=Severity.MEDIUM,
                remediation=(
                    "Добавьте заголовок: Strict-Transport-Security: max-age=31536000; includeSubDomains; preload"
                ),
                cvss_score=3.7,
                cwe_id="CWE-319",
                owasp_category="A05:2021",
                owasp_name="Security Misconfiguration",
                evidence="Заголовок отсутствует в ответе",
            ))
        else:
            # Check max-age
            if "max-age" in hsts.lower():
                try:
                    max_age = int(hsts.lower().split("max-age=")[1].split(";")[0].strip())
                    if max_age < 31536000:  # Less than 1 year
                        self._log_finding(self._create_finding(
                            title="Слишком малое значение HSTS max-age",
                            description=f"Значение HSTS max-age составляет {max_age}с, рекомендуемый минимум — 31536000с (1 год).",
                            severity=Severity.LOW,
                            remediation="Установите max-age не менее 31536000 (1 год).",
                            evidence=f"max-age={max_age}",
                        ))
                except (ValueError, IndexError):
                    pass

            if "includesubdomains" not in hsts.lower():
                self._log_finding(self._create_finding(
                    title="HSTS не применяется к поддоменам",
                    description="Заголовок HSTS не содержит директиву includeSubDomains.",
                    severity=Severity.LOW,
                    remediation="Добавьте includeSubDomains в заголовок HSTS.",
                    evidence=hsts,
                ))

    def _check_csp(self, response):
        """Check Content-Security-Policy header."""
        csp = response.headers.get("content-security-policy")

        if not csp:
            self._log_finding(self._create_finding(
                title="Отсутствует Content-Security-Policy",
                description=(
                    "Заголовок Content-Security-Policy не найден. CSP помогает предотвратить "
                    "XSS-атаки и инъекции данных, контролируя, какие ресурсы "
                    "браузеру разрешено загружать."
                ),
                severity=Severity.HIGH,
                remediation=(
                    "Реализуйте заголовок Content-Security-Policy. Начните с "
                    "ограничительной политики и постепенно добавляйте исключения по мере необходимости. "
                    "Пример: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'"
                ),
                cvss_score=6.1,
                cwe_id="CWE-693",
                owasp_category="A05:2021",
                owasp_name="Security Misconfiguration",
                evidence="Заголовок отсутствует в ответе",
            ))
        else:
            # Check for unsafe directives
            if "'unsafe-inline'" in csp and "script-src" in csp:
                self._log_finding(self._create_finding(
                    title="CSP разрешает unsafe-inline в script-src",
                    description="Content-Security-Policy разрешает инлайн-скрипты через 'unsafe-inline', что ослабляет защиту от XSS.",
                    severity=Severity.MEDIUM,
                    remediation="Удалите 'unsafe-inline' из script-src. Используйте nonce или хэши.",
                    evidence=csp[:200],
                ))

            if "'unsafe-eval'" in csp:
                self._log_finding(self._create_finding(
                    title="CSP разрешает unsafe-eval",
                    description="CSP разрешает eval() через 'unsafe-eval', что позволяет выполнять инъекции кода.",
                    severity=Severity.MEDIUM,
                    remediation="Удалите 'unsafe-eval' из директив CSP.",
                    evidence=csp[:200],
                ))

    def _check_x_content_type_options(self, response):
        """Check X-Content-Type-Options header."""
        xcto = response.headers.get("x-content-type-options")

        if not xcto or xcto.lower() != "nosniff":
            self._log_finding(self._create_finding(
                title="Отсутствует или некорректный X-Content-Type-Options",
                description=(
                    "Заголовок X-Content-Type-Options отсутствует или не установлен в 'nosniff'. "
                    "Это предотвращает атаки через MIME-сниффинг."
                ),
                severity=Severity.LOW,
                remediation="Установите X-Content-Type-Options: nosniff",
                evidence=f"Найдено: {xcto}" if xcto else "Не найден",
                cwe_id="CWE-693",
                owasp_category="A05:2021",
            ))

    def _check_xframe_options(self, response):
        """Check X-Frame-Options header."""
        xfo = response.headers.get("x-frame-options")
        csp_frame = response.headers.get("content-security-policy", "")

        has_protection = (
            (xfo and xfo.lower() in ("deny", "sameorigin")) or
            "frame-ancestors" in csp_frame.lower()
        )

        if not has_protection:
            self._log_finding(self._create_finding(
                title="Отсутствует защита от кликджекинга",
                description=(
                    "Ни X-Frame-Options, ни директива CSP frame-ancestors не установлены. "
                    "Сайт может быть уязвим к кликджекинг-атакам."
                ),
                severity=Severity.MEDIUM,
                remediation="Установите X-Frame-Options: DENY или используйте CSP frame-ancestors 'none'.",
                evidence="Защита от фрейминга не найдена",
                cwe_id="CWE-1021",
                owasp_category="A05:2021",
            ))

    def _check_referrer_policy(self, response):
        """Check Referrer-Policy header."""
        rp = response.headers.get("referrer-policy")

        if not rp:
            self._log_finding(self._create_finding(
                title="Отсутствует Referrer-Policy",
                description=(
                    "Заголовок Referrer-Policy не найден. Без него полные URL-адреса могут "
                    "передаваться как рефереры внешним сайтам."
                ),
                severity=Severity.LOW,
                remediation="Установите Referrer-Policy: strict-origin-when-cross-origin",
                evidence="Заголовок отсутствует",
            ))

    def _check_permissions_policy(self, response):
        """Check Permissions-Policy header."""
        pp = response.headers.get("permissions-policy")

        if not pp:
            self._log_finding(self._create_finding(
                title="Отсутствует Permissions-Policy",
                description=(
                    "Заголовок Permissions-Policy не найден. Этот заголовок контролирует, "
                    "какие функции браузера (камера, микрофон, геолокация и т.д.) "
                    "могут использоваться на сайте."
                ),
                severity=Severity.LOW,
                remediation=(
                    "Добавьте Permissions-Policy: camera=(), microphone=(), geolocation=()"
                ),
                evidence="Заголовок отсутствует",
            ))

    def _check_coop(self, response):
        """Check Cross-Origin-Opener-Policy."""
        coop = response.headers.get("cross-origin-opener-policy")

        if not coop:
            self._log_finding(self._create_finding(
                title="Отсутствует Cross-Origin-Opener-Policy",
                description="Заголовок COOP не установлен. Он помогает изолировать контексты просмотра.",
                severity=Severity.INFO,
                remediation="Установите Cross-Origin-Opener-Policy: same-origin",
                evidence="Заголовок отсутствует",
            ))

    def _check_corp(self, response):
        """Check Cross-Origin-Resource-Policy."""
        corp = response.headers.get("cross-origin-resource-policy")

        if not corp:
            self._log_finding(self._create_finding(
                title="Отсутствует Cross-Origin-Resource-Policy",
                description="Заголовок CORP не установлен. Он помогает предотвратить междоменное чтение ресурсов.",
                severity=Severity.INFO,
                remediation="Установите Cross-Origin-Resource-Policy: same-origin",
                evidence="Заголовок отсутствует",
            ))

    def _check_coep(self, response):
        """Check Cross-Origin-Embedder-Policy."""
        coep = response.headers.get("cross-origin-embedder-policy")

        if not coep:
            self._log_finding(self._create_finding(
                title="Отсутствует Cross-Origin-Embedder-Policy",
                description="Заголовок COEP не установлен.",
                severity=Severity.INFO,
                remediation="Установите Cross-Origin-Embedder-Policy: require-corp",
                evidence="Заголовок отсутствует",
            ))

    def _check_server_header(self, response):
        """Check if Server header exposes technology stack."""
        server = response.headers.get("server", "")
        powered_by = response.headers.get("x-powered-by", "")

        if server and any(kw in server.lower() for kw in ["apache", "nginx", "iis", "express"]):
            self._log_finding(self._create_finding(
                title="Заголовок Server раскрывает технологию",
                description=f"Заголовок Server раскрывает серверное ПО: {server}",
                severity=Severity.INFO,
                remediation="Удалите или замаскируйте заголовок Server.",
                evidence=f"Server: {server}",
            ))

        if powered_by:
            self._log_finding(self._create_finding(
                title="Обнаружен заголовок X-Powered-By",
                description=f"Заголовок X-Powered-By раскрывает технологию: {powered_by}",
                severity=Severity.LOW,
                remediation="Удалите заголовок X-Powered-By.",
                evidence=f"X-Powered-By: {powered_by}",
            ))
