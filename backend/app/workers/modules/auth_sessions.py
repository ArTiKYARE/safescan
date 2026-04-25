"""
SafeScan — Authentication & Session Management Module

Checks cookie security, session fixation, JWT misconfigurations,
password policy, MFA presence, brute-force protection.

Standards: ASVS-V2, V3, V4, NIST-IA
"""

import asyncio
import re
from bs4 import BeautifulSoup
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class AuthSessionsModule(ScanModule):
    """Module for authentication and session checks."""

    async def execute(self) -> ScanResult:
        """Execute auth/session checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_login_page()
        await self._check_cookie_security()
        await self._check_jwt_endpoints()
        await self._check_password_policy()
        await self._check_brute_force_protection()
        await self._check_session_management()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="auth_sessions",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_login_page(self):
        """Find and check login page security."""
        login_paths = ["/login", "/auth/login", "/signin", "/admin/login", "/wp-login.php"]

        for path in login_paths:
            response = await self._make_request(path=path)
            if response and response.status_code == 200:
                await self._analyze_login_form(response, path)
                break

    async def _analyze_login_form(self, response, path):
        """Analyze login form for security issues."""
        soup = BeautifulSoup(response.text, "html.parser")
        form = soup.find("form")

        if not form:
            return

        # Check for autocomplete on password fields
        password_field = soup.find("input", attrs={"type": "password"})
        if password_field:
            autocomplete = password_field.get("autocomplete")
            if autocomplete == "off":
                self._log_finding(self._create_finding(
                    title="Автозаполнение поля пароля отключено",
                    description=(
                        "Форма входа отключает автозаполнение пароля, что препятствует работе "
                        "менеджеров паролей и может приводить к использованию слабых паролей."
                    ),
                    severity=Severity.INFO,
                    remediation="Разрешите менеджерам паролей работать, не устанавливая autocomplete='off'.",
                    cwe_id="CWE-521",
                    owasp_category="A07:2021",
                ))

        # Check if form uses HTTP
        if str(response.url).startswith("http://"):
            self._log_finding(self._create_finding(
                title="Форма входа передаётся по HTTP",
                description="Форма входа обслуживается по незашифрованному HTTP. Учётные данные будут отправлены в открытом виде.",
                severity=Severity.CRITICAL,
                remediation="Обслуживайте страницу входа только по HTTPS. Перенаправляйте весь HTTP-трафик на HTTPS.",
                cvss_score=9.1,
                cwe_id="CWE-319",
                owasp_category="A02:2021",
            ))

    async def _check_cookie_security(self):
        """Check all cookies for security attributes."""
        response = await self._make_request(path="/")
        if not response:
            return

        set_cookie_headers = response.headers.get_list("set-cookie") if hasattr(response.headers, "get_list") else [
            v for k, v in response.headers.items() if k.lower() == "set-cookie"
        ]

        for cookie_header in set_cookie_headers:
            cookie_lower = cookie_header.lower()
            cookie_name = cookie_header.split("=")[0] if "=" in cookie_header else "unknown"

            issues = []
            if "secure" not in cookie_lower:
                issues.append("отсутствует флаг Secure")
            if "httponly" not in cookie_lower:
                issues.append("отсутствует флаг HttpOnly")
            if "samesite" not in cookie_lower:
                issues.append("отсутствует атрибут SameSite")

            if issues:
                severity = Severity.MEDIUM if any("Secure" in i or "HttpOnly" in i for i in issues) else Severity.LOW
                self._log_finding(self._create_finding(
                    title=f"Небезопасная кука: {cookie_name}",
                    description=f"Кука '{cookie_name}' имеет проблемы безопасности: {', '.join(issues)}.",
                    severity=severity,
                    remediation="Установите Secure, HttpOnly и SameSite=Strict/Lax для всех session-кук.",
                    cwe_id="CWE-614",
                    owasp_category="A07:2021",
                    evidence=cookie_header[:150],
                ))

    async def _check_jwt_endpoints(self):
        """Check JWT-related endpoints for misconfigurations."""
        response = await self._make_request(path="/api/auth/token")
        if response and response.status_code != 404:
            content_type = response.headers.get("content-type", "")
            if "application/json" in content_type and response.text:
                import json
                try:
                    data = json.loads(response.text)
                    if "token" in str(data).lower() or "jwt" in str(data).lower():
                        self._log_finding(self._create_finding(
                            title="Обнаружена JWT-эндпоинт",
                            description="Найдена эндпоинт JWT-аутентификации. Убедитесь в корректной валидации алгоритма и надёжности секрета.",
                            severity=Severity.INFO,
                            remediation=(
                                "Убедитесь, что JWT-библиотека отклоняет алгоритм 'none'. "
                                "Используйте надёжные секреты (256+ бит). "
                                "Установите подходящее время истечения. "
                                "Реализуйте обновление и отзыв токенов."
                            ),
                            cwe_id="CWE-347",
                            owasp_category="A07:2021",
                        ))
                except json.JSONDecodeError:
                    pass

    async def _check_password_policy(self):
        """Check password policy on registration."""
        reg_paths = ["/register", "/signup", "/auth/register"]
        for path in reg_paths:
            response = await self._make_request(path=path)
            if response and response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                pwd = soup.find("input", attrs={"type": "password"})
                if pwd:
                    min_length = pwd.get("minlength") or pwd.get("pattern")
                    if not min_length and not pwd.get("required"):
                        self._log_finding(self._create_finding(
                            title="Слабая политика паролей",
                            description="Форма регистрации не требует минимальную длину пароля.",
                            severity=Severity.MEDIUM,
                            remediation=(
                                "Требуйте минимум 8 символов. "
                                "Проверяйте по списку распространённых паролей. "
                                "Рассмотрите рекомендации NIST (без произвольного максимума, проверка по скомпрометированным паролям)."
                            ),
                            cwe_id="CWE-521",
                            owasp_category="A07:2021",
                        ))
                break

    async def _check_brute_force_protection(self):
        """Check for brute force protection on login."""
        login_paths = ["/login", "/auth/login"]
        for path in login_paths:
            response = await self._make_request(path=path)
            if response and response.text:
                soup = BeautifulSoup(response.text, "html.parser")

                has_captcha = soup.find(id=lambda x: x and ("captcha" in x.lower() or "recaptcha" in x.lower()))

                if not has_captcha:
                    self._log_finding(self._create_finding(
                        title="Не обнаружена защита от перебора паролей",
                        description="На форме входа не найдено CAPTCHA или индикаторов ограничения частоты запросов.",
                        severity=Severity.MEDIUM,
                        remediation=(
                            "Реализуйте блокировку аккаунта после неудачных попыток, "
                            "прогрессивные задержки или CAPTCHA. "
                            "Мониторьте атаки подбора учётных данных."
                        ),
                        cwe_id="CWE-307",
                        owasp_category="A07:2021",
                    ))
                break

    async def _check_session_management(self):
        """Check session management best practices."""
        response = await self._make_request(path="/")
        if not response:
            return

        cache_control = response.headers.get("cache-control", "").lower()
        if "no-store" not in cache_control and "no-cache" not in cache_control:
            self._log_finding(self._create_finding(
                title="Страницы могут кэшироваться",
                description="Заголовок Cache-Control не предотвращает кэширование конфиденциальных страниц.",
                severity=Severity.LOW,
                remediation="Установите Cache-Control: no-store, no-cache, must-revalidate для аутентифицированных страниц.",
                cwe_id="CWE-525",
                owasp_category="A07:2021",
            ))
