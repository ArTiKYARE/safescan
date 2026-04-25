"""
SafeScan — Application Logic Module

Checks for rate limiting, IDOR indicators, privilege escalation paths,
CAPTCHA presence, and business logic flaws.

Standards: OWASP-A04:2021, ASVS-V4
"""

import asyncio
from bs4 import BeautifulSoup
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class AppLogicModule(ScanModule):
    """Module for application logic checks."""

    async def execute(self) -> ScanResult:
        """Execute application logic checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_rate_limiting()
        await self._check_captcha_presence()
        await self._check_idor_indicators()
        await self._check_privilege_escalation()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="app_logic",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_rate_limiting(self):
        """Check for rate limiting on critical endpoints."""
        # Reduced from 5 to 3 endpoints for speed
        critical_endpoints = [
            "/login",
            "/auth/login",
            "/forgot-password",
        ]

        for endpoint in critical_endpoints:
            # Send rapid requests (reduced from 5 to 3 for speed)
            responses = []
            for i in range(3):
                response = await self._make_request(
                    path=endpoint,
                    method="POST",
                    data={"username": f"test{i}", "password": "test"},
                )
                if response:
                    responses.append(response)

            # Check for 429 Too Many Requests
            status_codes = [r.status_code for r in responses]
            if 429 in status_codes:
                # Rate limiting is in place — good
                pass
            elif len(responses) == 3:
                # No rate limiting detected
                self._log_finding(self._create_finding(
                    title=f"Отсутствует ограничение частоты запросов на {endpoint}",
                    description=(
                        f"Эндпоинт {endpoint} не имеет ограничения частоты запросов. "
                        f"Это позволяет атаки перебора или злоупотребления."
                    ),
                    severity=Severity.MEDIUM,
                    remediation=(
                        f"Реализуйте ограничение частоты запросов на {endpoint}. "
                        f"Используйте алгорит token bucket или sliding window. "
                        f"Рассмотрите CAPTCHA для пользовательских эндпоинтов."
                    ),
                    cvss_score=5.3,
                    cwe_id="CWE-770",
                    owasp_category="A04:2021",
                    owasp_name="Insecure Design",
                    affected_url=f"{self.base_url}{endpoint}",
                ))
                break

    async def _check_captcha_presence(self):
        """Check for CAPTCHA on forms that need it."""
        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        soup = BeautifulSoup(response.text, "html.parser")

        forms = soup.find_all("form")
        has_captcha = any(
            "captcha" in str(form).lower() or "recaptcha" in str(form).lower()
            for form in forms
        )

        if not has_captcha:
            has_recaptcha_script = any(
                "recaptcha" in str(script).lower()
                for script in soup.find_all("script")
            )

            if not has_recaptcha_script:
                self._log_finding(self._create_finding(
                    title="Не обнаружена защита CAPTCHA",
                    description=(
                        "На формах не найдено CAPTCHA, что делает их уязвимыми к "
                        "автоматизированному злоупотреблению (спам, перебор паролей, подбор учётных данных)."
                    ),
                    severity=Severity.LOW,
                    remediation=(
                        "Добавьте CAPTCHA (reCAPTCHA v3, hCaptcha) к пользовательским формам. "
                        "Используйте невидимую CAPTCHA для лучшего UX, где возможно."
                    ),
                    cwe_id="CWE-804",
                    owasp_category="A04:2021",
                ))

    async def _check_idor_indicators(self):
        """Check for Insecure Direct Object Reference indicators."""
        id_patterns = [
            r"/user/(\d+)",
            r"/profile/(\d+)",
            r"/account/(\d+)",
            r"/api/user/(\d+)",
            r"/api/v\d+/users/(\d+)",
            r"/order/(\d+)",
            r"/api/order/(\d+)",
            r"/document/(\d+)",
            r"/file/(\d+)",
        ]

        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        import re
        for pattern in id_patterns:
            matches = re.findall(pattern, response.text)
            if matches:
                self._log_finding(self._create_finding(
                    title="Потенциальный IDOR-эндпоинт",
                    description=(
                        f"Найден URL-паттерн {pattern} с числовыми ID. "
                        f"Убедитесь, что контроль доступа проверяет принадлежность ресурса пользователю."
                    ),
                    severity=Severity.INFO,
                    remediation=(
                        "Убедитесь, что все эндпоинты с ID ресурсов проверяют, "
                        "что аутентифицированный пользователь имеет разрешение на доступ "
                        "к этому конкретному ресурсу. Используйте UUID вместо последовательных ID."
                    ),
                    cwe_id="CWE-639",
                    owasp_category="A01:2021",
                    owasp_name="Broken Access Control",
                    evidence=f"Найден паттерн: {pattern}",
                ))
                break

    async def _check_privilege_escalation(self):
        """Check for privilege escalation indicators."""
        admin_paths = ["/admin", "/administrator", "/dashboard", "/panel"]

        for path in admin_paths:
            response = await self._make_request(path=path, follow_redirects=False)
            if response and response.status_code == 200:
                self._log_finding(self._create_finding(
                    title=f"Панель администратора может не требовать аутентификации: {path}",
                    description=(
                        f"Панель администратора по адресу {path} вернула 200 без перенаправления на вход. "
                        f"Убедитесь, что админ-зоны требуют надлежащую аутентификацию и авторизацию."
                    ),
                    severity=Severity.HIGH,
                    remediation=(
                        f"Реализуйте строгую аутентификацию для {path}. "
                        f"Используйте ролевой контроль доступа (RBAC). "
                        f"Реализуйте MFA для учётных записей администраторов."
                    ),
                    cvss_score=8.0,
                    cwe_id="CWE-862",
                    owasp_category="A01:2021",
                    affected_url=f"{self.base_url}{path}",
                ))
                break
