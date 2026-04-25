"""
SafeScan — Software Composition Analysis (SCA) Module

Detects vulnerable JS libraries, outdated frameworks, CMS detection,
and technology fingerprinting.

Standards: OWASP-A06:2021, NIST-SP 800-161
"""

import asyncio
import re
from bs4 import BeautifulSoup
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class SCAModule(ScanModule):
    """Module for dependency and component analysis."""

    # Known vulnerable library patterns (simplified database)
    VULNERABLE_LIBRARIES = {
        "jquery": {
            "safe_version": "3.5.0",
            "cve": "CVE-2020-11022",
            "description": "jQuery < 3.5.0 уязвим к XSS через функцию html()",
            "cvss": 6.1,
        },
        "angular.js": {
            "safe_version": "1.6.0",
            "cve": "CVE-2019-10762",
            "description": "AngularJS < 1.6.0 имеет уязвимость загрязнения прототипа",
            "cvss": 7.5,
        },
        "bootstrap": {
            "safe_version": "4.3.1",
            "cve": "CVE-2019-8331",
            "description": "Bootstrap < 4.3.1 имеет XSS в атрибуте data-target",
            "cvss": 6.1,
        },
        "moment": {
            "safe_version": "2.19.2",
            "cve": "CVE-2022-31129",
            "description": "Moment.js < 2.19.2 имеет уязвимость ReDoS",
            "cvss": 5.3,
        },
        "lodash": {
            "safe_version": "4.17.12",
            "cve": "CVE-2019-10744",
            "description": "Lodash < 4.17.12 имеет загрязнение прототипа",
            "cvss": 7.4,
        },
        "ckeditor": {
            "safe_version": "4.4.3",
            "cve": "CVE-2014-2319",
            "description": "CKEditor < 4.4.3 имеет XSS-уязвимость",
            "cvss": 6.1,
        },
        "tinymce": {
            "safe_version": "5.10.0",
            "cve": "CVE-2021-41340",
            "description": "TinyMCE < 5.10.0 имеет XSS через кастомные элементы",
            "cvss": 6.1,
        },
    }

    # CMS detection patterns
    CMS_PATTERNS = {
        "WordPress": ["/wp-content/", "/wp-includes/", "wp-json"],
        "Joomla": ["/media/jui/", "/media/system/", "option=com_"],
        "Drupal": ["/sites/default/", "Drupal.settings", "/core/misc/"],
        "Magento": ["/static/frontend/", "mage/"],
        "PrestaShop": ["/themes/default-bootstrap/", "/modules/"],
    }

    async def execute(self) -> ScanResult:
        """Execute SCA checks."""
        self.start_time = asyncio.get_event_loop().time()

        response = await self._make_request(path="/")
        if not response or not response.text:
            duration = asyncio.get_event_loop().time() - self.start_time
            return ScanResult(
                module="sca",
                findings=self.findings,
                success=False,
                error="Не удалось загрузить главную страницу",
                duration_seconds=duration,
            )

        await self._check_js_libraries(response)
        await self._check_cms_detection(response)
        await self._check_server_technology(response)

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="sca",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_js_libraries(self, response):
        """Check for known vulnerable JS libraries."""
        soup = BeautifulSoup(response.text, "html.parser")

        # Find all script tags
        scripts = soup.find_all("script", src=True)

        for script in scripts:
            src = script.get("src", "").lower()

            for lib_name, vuln_info in self.VULNERABLE_LIBRARIES.items():
                if lib_name.lower() in src:
                    # Extract version
                    version_match = re.search(
                        rf"{re.escape(lib_name.lower())}[.-/]?(\d+\.\d+\.?\d*)",
                        src,
                    )

                    if version_match:
                        version = version_match.group(1)
                        safe_version = vuln_info["safe_version"]

                        if self._compare_versions(version, safe_version) < 0:
                            self._log_finding(self._create_finding(
                                title=f"Уязвимая библиотека: {lib_name} {version}",
                                description=(
                                    f"{lib_name} версии {version} уязвима. "
                                    f"{vuln_info['description']}. "
                                    f"Безопасная версия: {safe_version}+"
                                ),
                                severity=Severity.HIGH if vuln_info["cvss"] >= 7.0 else Severity.MEDIUM,
                                remediation=f"Обновите {lib_name} до версии {safe_version} или выше.",
                                cvss_score=vuln_info["cvss"],
                                cwe_id="CWE-1104",
                                owasp_category="A06:2021",
                                owasp_name="Vulnerable and Outdated Components",
                                evidence=f"Script src: {src}",
                            ))

        # Also check inline version comments
        comments = soup.find_all(string=lambda text: isinstance(text, str) and "<!--" in str(text))
        for comment in comments:
            for lib_name, vuln_info in self.VULNERABLE_LIBRARIES.items():
                if lib_name.lower() in str(comment).lower():
                    version_match = re.search(
                        rf"{re.escape(lib_name.lower())}\s+v?(\d+\.\d+\.?\d*)",
                        str(comment),
                        re.IGNORECASE,
                    )
                    if version_match:
                        version = version_match.group(1)
                        if self._compare_versions(version, vuln_info["safe_version"]) < 0:
                            self._log_finding(self._create_finding(
                                title=f"Устаревшая библиотека: {lib_name} {version}",
                                description=f"Комментарий раскрывает {lib_name} {version} (безопасная: {vuln_info['safe_version']}+).",
                                severity=Severity.LOW,
                                remediation=f"Обновите {lib_name} и удалите комментарии с версиями.",
                                evidence=str(comment)[:100],
                            ))

    async def _check_cms_detection(self, response):
        """Detect CMS platform."""
        for cms, patterns in self.CMS_PATTERNS.items():
            for pattern in patterns:
                if pattern in response.text.lower():
                    self._log_finding(self._create_finding(
                        title=f"Обнаружена CMS: {cms}",
                        description=(
                            f"Обнаружена CMS {cms}. Убедитесь, что она обновлена до последней "
                            f"версии и все плагины/темы пропатчены."
                        ),
                        severity=Severity.INFO,
                        remediation=(
                            f"Поддерживайте ядро {cms}, плагины и темы в актуальном состоянии. "
                            f"Удалите неиспользуемые плагины/темы. "
                            f"Используйте плагины безопасности (WAF, защита входа)."
                        ),
                        evidence=f"Обнаружен паттерн: {pattern}",
                    ))
                    break

    async def _check_server_technology(self, response):
        """Detect server-side technology from headers."""
        server = response.headers.get("server", "").lower()
        x_powered_by = response.headers.get("x-powered-by", "").lower()

        technologies = {
            "php": ("PHP", "Убедитесь, что PHP обновлён до 8.1+ (7.x больше не поддерживается)"),
            "node.js": ("Node.js", "Убедитесь, что Express и зависимости обновлены"),
            "express": ("Express", "Проверьте известные уязвимости Express"),
            "asp.net": ("ASP.NET", "Убедитесь, что .NET Framework обновлён"),
            "python": ("Python", "Убедитесь, что фреймворк (Django/Flask) обновлён"),
            "django": ("Django", "Проверьте версию Django на известные CVE"),
            "rails": ("Ruby on Rails", "Убедитесь, что Rails и gems обновлены"),
            "java": ("Java", "Проверьте версию сервера приложений"),
            "tomcat": ("Apache Tomcat", "Обновите Tomcat до последней стабильной версии"),
        }

        for tech_key, (tech_name, recommendation) in technologies.items():
            if tech_key in server or tech_key in x_powered_by:
                self._log_finding(self._create_finding(
                    title=f"Обнаружена технология: {tech_name}",
                    description=f"Определена серверная технология: {tech_name}",
                    severity=Severity.INFO,
                    remediation=recommendation,
                    evidence=f"Server: {server}, X-Powered-By: {x_powered_by}",
                ))

    def _compare_versions(self, v1: str, v2: str) -> int:
        """Compare version strings. Returns -1, 0, or 1."""
        v1_parts = [int(x) for x in v1.split(".")]
        v2_parts = [int(x) for x in v2.split(".")]

        # Pad shorter version with zeros
        while len(v1_parts) < len(v2_parts):
            v1_parts.append(0)
        while len(v2_parts) < len(v1_parts):
            v2_parts.append(0)

        for a, b in zip(v1_parts, v2_parts):
            if a < b:
                return -1
            if a > b:
                return 1
        return 0
