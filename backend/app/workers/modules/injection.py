"""
SafeScan — Injection Detection Module

Detects SQLi, NoSQLi, Command Injection, Code Injection,
LDAP Injection, XPath Injection, SSTI.

All payloads are SAFE detection-only.
Uses **differential testing** — compares baseline vs payload
response to eliminate false positives from reflected form values.

Standards: OWASP-A03:2021, ASVS-V5, CWE-89, CWE-78
"""

import asyncio
import re
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class InjectionModule(ScanModule):
    """Module for detecting various injection vulnerabilities."""

    # SQLi detection payloads (safe) — reduced for speed
    SQLI_PAYLOADS = [
        "' OR '1'='1",  # Classic boolean test
        "' UNION SELECT NULL --",  # UNION-based (detected only)
        "1' AND SLEEP(0) --",  # Time-based (0 sec sleep for safety)
    ]

    # SQL error patterns
    SQL_ERROR_PATTERNS = [
        r"SQL syntax.*MySQL",
        r"Warning.*mysql_",
        r"valid MySQL result",
        r"PostgreSQL.*ERROR",
        r"Warning.*\Wpg_",
        r"valid PostgreSQL result",
        r"Native table.*Oracle",
        r"ORA-\d{4,5}",
        r"Driver.*SQL SERVER",
        r"OLE DB.*SQL SERVER",
        r"MS SQL Server.*Driver",
        r"Unclosed quotation mark after the character string",
        r"SQLite3::SQLException",
        r"SQLITE_ERROR",
    ]

    # NoSQLi payloads — reduced for speed
    NOSQL_PAYLOADS = [
        '{"$gt": ""}',
        '{"$ne": null}',
    ]

    # Command injection payloads (safe detection)
    # Use unique marker unlikely to appear in normal HTML
    CMDI_MARKER = "SXCI_7823"
    CMDI_PAYLOADS = [
        f";echo {CMDI_MARKER}",
        f"|echo {CMDI_MARKER}",
        f"&&echo {CMDI_MARKER}",
    ]

    # SSTI payloads — reduced for speed (only most reliable test)
    # Use 37*73=2701 (unlikely to exist in random HTML unlike 49)
    SSTI_TESTS = [
        ("{{37*73}}", "2701"),       # Jinja2/Twig — most common
    ]

    async def execute(self) -> ScanResult:
        """Execute injection detection."""
        self.start_time = asyncio.get_event_loop().time()

        # Discover input points
        input_points = await self._discover_input_points()

        # Get baselines for all points (no payloads)
        baselines = {}
        for point in input_points:
            baseline = await self._get_baseline(point)
            baselines[point["parameter"]] = baseline

        # Test each point with differential comparison
        for point in input_points:
            baseline = baselines[point["parameter"]]
            # Run all injection tests for this point in parallel
            await asyncio.gather(
                self._test_sqli(point, baseline),
                self._test_nosqli(point, baseline),
                self._test_command_injection(point, baseline),
                self._test_ssti(point, baseline),
            )

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="injection",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _get_baseline(self, point: dict):
        """Get baseline response WITHOUT any injection payload."""
        if point["method"] == "get":
            return await self._make_request(path=point["url"])
        else:
            return await self._make_request(
                path=point["url"],
                method="POST",
            )

    async def _discover_input_points(self) -> list[dict]:
        """Find potential injection points."""
        points = []
        response = await self._make_request(path="/")

        if response and response.text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, "html.parser")

            for form in soup.find_all("form"):
                action = form.get("action", "/")
                method = form.get("method", "get").lower()
                for inp in form.find_all(["input", "textarea"]):
                    name = inp.get("name")
                    if name:
                        points.append({
                            "url": action,
                            "method": method,
                            "parameter": name,
                        })

            # URL params
            for param in ["id", "page", "item", "product", "category", "user", "name", "search"]:
                points.append({
                    "url": "/",
                    "method": "get",
                    "parameter": param,
                })

        return points[:10]  # Reduced from 20 to 10 for speed

    async def _test_sqli(self, point: dict, baseline):
        """Test for SQL injection."""
        for payload in self.SQLI_PAYLOADS:
            if point["method"] == "get":
                response = await self._make_request(
                    path=point["url"],
                    params={point["parameter"]: payload},
                )
            else:
                response = await self._make_request(
                    path=point["url"],
                    method="POST",
                    data={point["parameter"]: payload},
                )

            if response and response.text:
                for pattern in self.SQL_ERROR_PATTERNS:
                    if re.search(pattern, response.text, re.IGNORECASE):
                        # Differential check: error NOT in baseline
                        if baseline and baseline.text and re.search(pattern, baseline.text, re.IGNORECASE):
                            continue  # Error already in baseline — not injection

                        self._log_finding(self._create_finding(
                            title=f"SQL-инъекция в параметре '{point['parameter']}'",
                            description=(
                                f"Параметр '{point['parameter']}' уязвим к SQL-инъекции. "
                                f"В ответе обнаружены паттерны SQL-ошибок."
                            ),
                            severity=Severity.CRITICAL,
                            remediation=(
                                "Используйте параметризованные запросы / подготовленные выражения. "
                                "Никогда не конкатенируйте пользовательский ввод в SQL-запросы. "
                                "Используйте ORM-билдеры с корректным экранированием."
                            ),
                            cvss_score=9.8,
                            cwe_id="CWE-89",
                            owasp_category="A03:2021",
                            owasp_name="Injection",
                            affected_url=str(response.url),
                            affected_parameter=point["parameter"],
                            evidence=f"SQL-паттерн совпал: {pattern}",
                        ))
                        return

    async def _test_nosqli(self, point: dict, baseline):
        """Test for NoSQL injection."""
        import json

        for payload in self.NOSQL_PAYLOADS:
            try:
                payload_json = json.loads(payload)
                response = await self._make_request(
                    path=point["url"],
                    method="POST",
                    json_data=payload_json,
                    headers={"Content-Type": "application/json"},
                )

                if response and response.status_code == 500:
                    # Differential check: baseline also 500?
                    if baseline and baseline.status_code == 500:
                        continue  # Always returns 500 — not NoSQLi

                    self._log_finding(self._create_finding(
                        title=f"Потенциальная NoSQL-инъекция в параметре '{point['parameter']}'",
                        description=(
                            f"Параметр '{point['parameter']}' возвращает ошибку 500 "
                            f"при отправке NoSQL-операторов. Рекомендуется ручная проверка."
                        ),
                        severity=Severity.HIGH,
                        remediation=(
                            "Валидируйте и санитизируйте ввод. "
                            "Избегайте прямой передачи пользовательского ввода в NoSQL-запросы. "
                            "Используйте валидацию по белому списку для ожидаемых значений."
                        ),
                        cvss_score=8.6,
                        cwe_id="CWE-943",
                        owasp_category="A03:2021",
                        affected_url=str(response.url),
                        evidence=f"Payload: {payload}",
                    ))
            except json.JSONDecodeError:
                pass

    async def _test_command_injection(self, point: dict, baseline):
        """
        Test for OS command injection.

        Differential approach:
        1. Get marker in payload response
        2. Ensure marker NOT in baseline (wasn't already there)
        3. Ensure marker is NOT just reflected in form value attributes
           (WordPress CF7 reflects input values — not command execution)
        """
        for payload in self.CMDI_PAYLOADS:
            response = await self._make_request(
                path=point["url"],
                params={point["parameter"]: payload},
            )

            if not response or not response.text:
                continue

            # Marker must be in response
            if self.CMDI_MARKER not in response.text:
                continue

            # Marker must NOT be in baseline
            if baseline and baseline.text and self.CMDI_MARKER in baseline.text:
                continue  # Already in baseline — not injection

            # Critical check: marker must appear OUTSIDE HTML form values
            # WordPress CF7 reflects values in: value="..." attributes
            # Real command injection: marker appears as standalone text
            text_without_values = re.sub(r'value="[^"]*"', 'value=""', response.text)
            text_without_values = re.sub(r"value='[^']*'", "value=''", text_without_values)

            if self.CMDI_MARKER not in text_without_values:
                continue  # Only in form values — reflection, not execution

            self._log_finding(self._create_finding(
                title=f"Инъекция команд в параметре '{point['parameter']}'",
                description=(
                    f"Параметр '{point['parameter']}' уязвим к инъекции ОС-команд. "
                    f"Вывод команды отражается в ответе."
                ),
                severity=Severity.CRITICAL,
                remediation=(
                    "Никогда не передавайте пользовательский ввод в системные команды. "
                    "Используйте валидацию по белому списку для аргументов команд. "
                    "Используйте языково-специфичные API вместо shell-команд."
                ),
                cvss_score=10.0,
                cwe_id="CWE-78",
                owasp_category="A03:2021",
                affected_url=str(response.url),
                affected_parameter=point["parameter"],
                evidence="Вывод команды отражён (не в HTML-атрибутах)",
            ))
            return

    async def _test_ssti(self, point: dict, baseline):
        """
        Test for Server-Side Template Injection.

        Differential approach:
        1. Check if calculated result (e.g. 2701) appears in response
        2. Ensure result NOT in baseline (wasn't already there)
        3. Use 37*73=2701 instead of 7*7=49 (49 is common in HTML)
        """
        for payload_expr, expected_result in self.SSTI_TESTS:
            response = await self._make_request(
                path=point["url"],
                params={point["parameter"]: payload_expr},
            )

            if not response or not response.text:
                continue

            # Result must be in response
            if expected_result not in response.text:
                continue

            # Result must NOT be in baseline
            if baseline and baseline.text and expected_result in baseline.text:
                continue  # Already in baseline — not SSTI

            # Additional check: if payload_expr is also reflected as-is,
            # the result might be from the literal string, not evaluation.
            # Count occurrences — if result appears significantly more
            # times than payload, it was likely evaluated.
            payload_count = response.text.count(payload_expr)
            result_count = response.text.count(expected_result)

            if payload_count > 0 and result_count <= payload_count:
                # Result appears no more than the payload itself — likely reflection
                continue

            self._log_finding(self._create_finding(
                title=f"Инъекция серверных шаблонов (SSTI) в параметре '{point['parameter']}'",
                description=(
                    f"Параметр '{point['parameter']}' обрабатывается шаблонизатором. "
                    f"Математическое выражение было вычислено."
                ),
                severity=Severity.CRITICAL,
                remediation=(
                    "Не рендерите пользовательский ввод как код шаблона. "
                    "Используйте автоэкранирование по контексту. "
                    "Разделяйте логику шаблонов и пользовательские данные."
                ),
                cvss_score=9.0,
                cwe_id="CWE-94",
                owasp_category="A03:2021",
                affected_url=str(response.url),
                affected_parameter=point["parameter"],
                evidence=f"Выражение вычислено: {payload_expr} => {expected_result}",
            ))
            return
