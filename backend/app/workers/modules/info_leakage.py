"""
SafeScan — Information Leakage Module

Detects .git, .env, backup files, API keys in JS, email/phone in source,
metadata exposure, and sensitive file access.

Standards: OWASP-A01:2021, ASVS-V8, GDPR, 152-ФЗ
"""

import asyncio
import re
from bs4 import BeautifulSoup
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class InfoLeakageModule(ScanModule):
    """Module for detecting information leakage and data exposure."""

    # Sensitive files to check
    SENSITIVE_FILES = [
        # Version control
        "/.git/HEAD",
        "/.git/config",
        "/.svn/entries",
        "/.hg/.hgignore",

        # Environment & config
        "/.env",
        "/.env.local",
        "/.env.production",
        "/.env.development",
        "/config/.env",
        "/.env.bak",
        "/wp-config.php.bak",

        # Backup files
        "/backup.sql",
        "/backup.tar.gz",
        "/backup.zip",
        "/db.sql",
        "/dump.sql",
        "/database.sql",
        "/site.tar.gz",
        "/www.tar.gz",
        "/backup/",

        # Development/IDE files
        "/.DS_Store",
        "/Thumbs.db",
        "/.idea/",
        "/.vscode/",
        "/.project",
        "/composer.lock",
        "/package-lock.json",
        "/yarn.lock",
        "/pom.xml",

        # Logs
        "/logs/",
        "/log/",
        "/error.log",
        "/access.log",
        "/debug.log",

        # Config
        "/config.php",
        "/config.yml",
        "/config.json",
        "/database.yml",
        "/web.config",

        # Temp files
        "/tmp/",
        "/temp/",
        "/cache/",
    ]

    # API key and secret patterns (regex)
    SECRET_PATTERNS = [
        (r"(?:aws_access_key_id|AWS_ACCESS_KEY_ID)\s*[:=]\s*[A-Za-z0-9/+=]{20}", "AWS Access Key ID"),
        (r"(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[:=]\s*[A-Za-z0-9/+=]{40}", "AWS Secret Key"),
        (r"sk-[a-zA-Z0-9]{20,}", "Секретный ключ (общий)"),
        (r"ghp_[a-zA-Z0-9]{36}", "GitHub Personal Access Token"),
        (r"gho_[a-zA-Z0-9]{36}", "GitHub OAuth Token"),
        (r"xox[baprs]-[a-zA-Z0-9\-]+", "Slack Token"),
        (r"AIza[0-9A-Za-z\-_]{35}", "Google API Key"),
        (r"EAACEdEose0cBA[0-9A-Za-z]+", "Facebook Access Token"),
        (r"access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}", "PayPal/Braintree Token"),
        (r"sq0atp-[0-9A-Za-z\-_]{22}", "Square Access Token"),
        (r"pmkey-[a-zA-Z0-9\-_]{20,}", "Идентификатор приватного ключа"),
        (r"(?:password|passwd|pwd)\s*[:=]\s*['\"][^\s'\"]{8,}['\"]", "Жёстко заданный пароль"),
    ]

    # PII patterns
    PII_PATTERNS = [
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "адрес email"),
        (r"\b\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b", "номер телефона (US)"),
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "номер кредитной карты"),
    ]

    async def execute(self) -> ScanResult:
        """Execute information leakage checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_sensitive_files()
        await self._check_source_code_leaks()
        await self._check_api_keys_in_js()
        await self._check_metadata()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="info_leakage",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_sensitive_files(self):
        """Check for accessible sensitive files."""
        # Process files in parallel batches of 10 for speed
        batch_size = 10
        
        for i in range(0, len(self.SENSITIVE_FILES), batch_size):
            batch = self.SENSITIVE_FILES[i:i + batch_size]
            
            # Create tasks for parallel execution
            tasks = [self._check_single_file(file_path) for file_path in batch]
            await asyncio.gather(*tasks)

    async def _check_single_file(self, file_path: str):
        """Check a single sensitive file."""
        response = await self._make_request(path=file_path)

        if response and response.status_code == 200:
            content_length = len(response.text)

            if content_length > 10:
                severity = Severity.CRITICAL if file_path.startswith("/.git") or file_path.startswith("/.env") else Severity.HIGH

                title_map = {
                    "/.git/": "Git-репозиторий в открытом доступе",
                    "/.env": "Файл окружения в открытом доступе",
                    ".sql": "Резервная копия БД в открытом доступе",
                    "/config": "Файл конфигурации в открытом доступе",
                    "/logs": "Файлы логов в открытом доступе",
                }

                title = "Доступ к конфиденциальному файлу"
                for key, t in title_map.items():
                    if key in file_path:
                        title = t
                        break

                self._log_finding(self._create_finding(
                    title=f"{title}: {file_path}",
                    description=(
                        f"Конфиденциальный файл {file_path} общедоступен. "
                        f"Это может раскрыть учётные данные, конфигурацию или персональные данные."
                    ),
                    severity=severity,
                    remediation=(
                        f"Заблокируйте доступ к {file_path} через конфигурацию веб-сервера.\n"
                        f"Добавьте в .htaccess или Nginx:\n"
                        f"  location ~ /\. {{ deny all; }}\n"
                        f"Удалите конфиденциальные файлы из корня веб-сервера."
                    ),
                    cvss_score=9.1 if severity == Severity.CRITICAL else 7.5,
                    cwe_id="CWE-200",
                    owasp_category="A01:2021",
                    affected_url=f"{self.base_url}{file_path}",
                    evidence=f"Файл доступен: {content_length} байт",
                ))

    async def _check_source_code_leaks(self):
        """Check for information in HTML source code."""
        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        # Check for emails in source
        for pattern, name in self.PII_PATTERNS[:1]:  # Just email for now
            matches = re.findall(pattern, response.text)
            if matches:
                unique_emails = set(matches)
                if unique_emails:
                    self._log_finding(self._create_finding(
                        title=f"Персональные данные в исходном коде: {name.capitalize()}",
                        description=f"Найдено {len(unique_emails)} {name} в HTML-коде.",
                        severity=Severity.LOW,
                        remediation="Удалите персональные данные из исходного кода. Используйте контактные формы.",
                        cwe_id="CWE-200",
                        evidence=f"Пример: {list(unique_emails)[:3]}",
                    ))

    async def _check_api_keys_in_js(self):
        """Check JavaScript files for API keys and secrets."""
        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        js_urls = [s.get("src") for s in soup.find_all("script", src=True)]

        # Also check inline scripts
        for script in soup.find_all("script"):
            if script.string:
                self._check_content_for_secrets(script.string, "inline script")

        # Check external JS files (limit to 10)
        for js_url in js_urls[:10]:
            js_response = await self._make_request(url=js_url)
            if js_response and js_response.text:
                self._check_content_for_secrets(js_response.text, js_url)

    def _check_content_for_secrets(self, content: str, source: str):
        """Check content for secret patterns."""
        for pattern, secret_name in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                self._log_finding(self._create_finding(
                    title=f"Секрет в JavaScript-коде: {secret_name}",
                    description=(
                        f"Обнаружен потенциальный {secret_name} в {source}. "
                        f"API-ключи и секреты никогда не должны находиться в клиентском коде."
                    ),
                    severity=Severity.HIGH,
                    remediation=(
                        f"Удалите {secret_name} из клиентского кода. "
                        f"Используйте серверные API-запросы с надлежащей аутентификацией. "
                        f"Немедленно отозвите раскрытый ключ."
                    ),
                    cvss_score=7.5,
                    cwe_id="CWE-798",
                    owasp_category="A01:2021",
                    evidence=f"Паттерн совпал: {secret_name} (первые 30 символов: {matches[0][:30]}...)",
                ))

    async def _check_metadata(self):
        """Check for metadata exposure."""
        # Reduced to essential metadata paths only
        metadata_paths = [
            "/robots.txt",
            "/sitemap.xml",
            "/.well-known/security.txt",
        ]

        # Check metadata paths in parallel
        tasks = [self._check_metadata_path(path) for path in metadata_paths]
        await asyncio.gather(*tasks)

    async def _check_metadata_path(self, path: str):
        """Check a single metadata path."""
        response = await self._make_request(path=path)
        if response and response.status_code == 200:
            if "disallow: /" in response.text.lower() and path == "/robots.txt":
                self._log_finding(self._create_finding(
                    title="Широкое ограничение Disallow в robots.txt",
                    description="robots.txt запрещает сканирование многих путей, что может раскрыть скрытые директории.",
                    severity=Severity.INFO,
                    remediation="Проверьте robots.txt, чтобы убедиться, что он не раскрывает конфиденциальные пути.",
                    evidence="Обнаружено Disallow: /",
                ))
