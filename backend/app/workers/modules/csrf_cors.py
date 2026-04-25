"""
SafeScan — CSRF & CORS Module

Detects CSRF misconfigurations and CORS issues.
Standards: OWASP-A01:2021, ASVS-V4
"""

import asyncio
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class CSRFCORSModule(ScanModule):
    """Module for CSRF and CORS checks."""

    async def execute(self) -> ScanResult:
        """Execute CSRF/CORS checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_csrf()
        await self._check_cors()
        await self._check_cookie_attributes()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="csrf_cors",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_csrf(self):
        """Check for CSRF token presence on forms."""
        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Find state-changing forms (POST, PUT, DELETE)
        for form in soup.find_all("form"):
            method = form.get("method", "get").lower()
            if method not in ("post", "put", "delete", "patch"):
                continue

            # Check for CSRF token
            csrf_fields = form.find_all(
                "input",
                attrs={"name": lambda x: x and "csrf" in x.lower()}
            )
            hidden_tokens = form.find_all(
                "input",
                attrs={"type": "hidden", "name": lambda x: x and "token" in x.lower()}
            )

            if not csrf_fields and not hidden_tokens:
                action = form.get("action", "/")
                self._log_finding(self._create_finding(
                    title="Отсутствует CSRF-токен в форме",
                    description=(
                        f"Форма, отправляющая данные на {action} методом {method.upper()}, "
                        f"не содержит CSRF-токена. Это позволяет проводить атаки "
                        f"межсайтовой подделки запросов."
                    ),
                    severity=Severity.HIGH,
                    remediation=(
                        "Добавьте CSRF-токен как скрытое поле во все формы, изменяющие состояние. "
                        "Используйте атрибут SameSite для кук как дополнительную защиту. "
                        "Реализуйте паттерн double-submit cookie для API."
                    ),
                    cvss_score=6.5,
                    cwe_id="CWE-352",
                    owasp_category="A01:2021",
                    owasp_name="Broken Access Control",
                    affected_url=str(response.url),
                    evidence=f"Form action: {action}, method: {method}",
                ))

    async def _check_cors(self):
        """Check CORS configuration."""
        origins_to_test = [
            "null",
            "https://evil.com",
            "http://evil.com",
            f"{self.base_url}",
        ]

        for origin in origins_to_test:
            response = await self._make_request(
                path="/",
                headers={"Origin": origin},
            )

            if response:
                acao = response.headers.get("access-control-allow-origin")
                acac = response.headers.get("access-control-allow-credentials")

                # Check for wildcard origin
                if acao == "*":
                    self._log_finding(self._create_finding(
                        title="CORS разрешает все источники (wildcard)",
                        description=(
                            "Access-Control-Allow-Origin установлен в '*', что позволяет любому "
                            "сайту отправлять запросы к этому API."
                        ),
                        severity=Severity.MEDIUM,
                        remediation=(
                            "Ограничьте Access-Control-Allow-Origin конкретными доверенными доменами. "
                            "Никогда не используйте '*' для API с конфиденциальными данными."
                        ),
                        cvss_score=5.3,
                        cwe_id="CWE-942",
                        owasp_category="A01:2021",
                        evidence="Access-Control-Allow-Origin: *",
                    ))
                    break

                # Check for credentials + wildcard
                if acao == "*" and acac == "true":
                    self._log_finding(self._create_finding(
                        title="CORS: wildcard с передачей учётных данных",
                        description=(
                            "CORS разрешает wildcard-происхождение (*) вместе с учётными данными (true). "
                            "Это критическая ошибка конфигурации."
                        ),
                        severity=Severity.CRITICAL,
                        remediation="Никогда не комбинируйте wildcard-происхождение с Access-Control-Allow-Credentials: true.",
                        cvss_score=9.1,
                        cwe_id="CWE-942",
                        owasp_category="A01:2021",
                        evidence="Wildcard + Credentials",
                    ))
                    break

                # Check for null origin
                if acao == "null":
                    self._log_finding(self._create_finding(
                        title="CORS разрешает происхождение null",
                        description=(
                            "Сервер разрешает происхождение 'null', которое может быть отправлено "
                            "песочечными iframe."
                        ),
                        severity=Severity.HIGH,
                        remediation="Не разрешайте 'null' как доверенное происхождение.",
                        cvss_score=6.5,
                        cwe_id="CWE-942",
                        evidence="Access-Control-Allow-Origin: null",
                    ))

    async def _check_cookie_attributes(self):
        """Check cookie security attributes."""
        response = await self._make_request(path="/")
        if not response:
            return

        # Check Set-Cookie headers
        for header_name, header_value in response.headers.items():
            if header_name.lower() == "set-cookie":
                cookie_lower = header_value.lower()

                if "secure" not in cookie_lower:
                    self._log_finding(self._create_finding(
                        title="У куки отсутствует флаг Secure",
                        description="Кука устанавливается без флага Secure, что позволяет передачу по HTTP.",
                        severity=Severity.MEDIUM,
                        remediation="Добавьте флаг Secure ко всем кукам.",
                        cvss_score=5.3,
                        cwe_id="CWE-614",
                        owasp_category="A01:2021",
                        evidence=header_value[:100],
                    ))

                if "httponly" not in cookie_lower and "session" in cookie_lower:
                    self._log_finding(self._create_finding(
                        title="У session-куки отсутствует флаг HttpOnly",
                        description="Session-кука доступна через JavaScript (отсутствует флаг HttpOnly).",
                        severity=Severity.MEDIUM,
                        remediation="Добавьте флаг HttpOnly к session-кукам.",
                        cvss_score=5.3,
                        cwe_id="CWE-1004",
                        owasp_category="A07:2021",
                        evidence=header_value[:100],
                    ))

                if "samesite" not in cookie_lower:
                    self._log_finding(self._create_finding(
                        title="У куки отсутствует атрибут SameSite",
                        description="Кука не имеет атрибута SameSite, что облегчает CSRF-атаки.",
                        severity=Severity.LOW,
                        remediation="Установите SameSite=Strict или SameSite=Lax для кук.",
                        cwe_id="CWE-1275",
                        owasp_category="A01:2021",
                        evidence=header_value[:100],
                    ))
