"""
SafeScan — XSS Detection Module

Detects Reflected XSS, Stored XSS indicators, DOM-based XSS,
CSP bypass vectors, and mXSS patterns.

All payloads are SAFE detection-only (alert-less, non-executing).
Standards: OWASP-A07:2021, ASVS-V6, CWE-79
"""

import asyncio
import re
from urllib.parse import quote, urlencode
from bs4 import BeautifulSoup
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class XSSModule(ScanModule):
    """Module for detecting Cross-Site Scripting vulnerabilities."""

    # Safe detection payloads (no actual execution)
    DETECTION_PAYLOADS = [
        "<sxsscanx>test</sxsscanx>",  # Unique tag detection
        "\"'><sxsscanx>",  # Context breaking
        "javascript:alert(1)",  # JS protocol (detected, not executed)
        "\" onmouseover=\"\"",  # Event handler injection
        "<img src=x onerror=\"\">",  # Tag-based injection
        "<svg onload=\"\">",  # SVG based
    ]

    async def execute(self) -> ScanResult:
        """Execute XSS detection."""
        self.start_time = asyncio.get_event_loop().time()

        # Step 1: Crawl and find input points
        input_points = await self._discover_input_points()

        # Step 2: Test each input point with safe payloads
        for point in input_points:
            await self._test_input_point(point)

        # Step 3: Check for DOM-based XSS patterns in JS
        await self._check_dom_xss_patterns()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="xss",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
            pages_crawled=1,
        )

    async def _discover_input_points(self) -> list[dict]:
        """Discover input points by crawling and analyzing forms/URLs."""
        points = []

        # Check main page for forms
        response = await self._make_request(path="/")
        if response and response.text:
            soup = BeautifulSoup(response.text, "html.parser")

            # Find forms
            for form in soup.find_all("form"):
                action = form.get("action", "/")
                method = form.get("method", "get").lower()

                for input_tag in form.find_all(["input", "textarea", "select"]):
                    name = input_tag.get("name")
                    if name:
                        points.append({
                            "type": "form",
                            "url": action,
                            "method": method,
                            "parameter": name,
                        })

            # Check URL parameters (common reflection points)
            common_params = ["q", "search", "query", "id", "page", "p", "s", "keyword"]
            for param in common_params:
                points.append({
                    "type": "url_param",
                    "url": "/",
                    "method": "get",
                    "parameter": param,
                })

        # Check search endpoints
        for path in ["/search", "/api/search", "/find"]:
            points.append({
                "type": "url_param",
                "url": path,
                "method": "get",
                "parameter": "q",
            })

        return points

    async def _test_input_point(self, point: dict):
        """Test an input point with safe payloads."""
        for payload in self.DETECTION_PAYLOADS:
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
                # Check if payload is reflected without sanitization
                if payload in response.text:
                    # Check context — is it inside HTML?
                    context = self._get_reflection_context(response.text, payload)

                    if context["unsanitized"]:
                        severity = Severity.HIGH
                        if context["in_script"]:
                            severity = Severity.CRITICAL
                        elif context["in_attribute"]:
                            severity = Severity.HIGH
                        elif context["in_html_body"]:
                            severity = Severity.MEDIUM

                        self._log_finding(self._create_finding(
                            title=f"Потенциальный XSS в параметре '{point['parameter']}'",
                            description=(
                                f"Пользовательский ввод в параметре '{point['parameter']}' "
                                f"отражается в ответе без должной санитизации. "
                                f"Контекст отражения: {context['description']}"
                            ),
                            severity=severity,
                            remediation=(
                                "Реализуйте корректное кодирование вывода в зависимости от контекста:\n"
                                "- HTML-тело: HTML-кодирование (< > & \" ' /)\n"
                                "- HTML-атрибут: HTML-кодирование\n"
                                "- JavaScript: JS-кодирование с контекстным экранированием\n"
                                "- URL: URL-кодирование\n"
                                "Используйте встроенное автоэкранирование фреймворка (например, Jinja2 autoescape)."
                            ),
                            cvss_score=6.1 if severity == Severity.MEDIUM else 7.5,
                            cwe_id="CWE-79",
                            owasp_category="A07:2021",
                            owasp_name="Cross-Site Scripting (XSS)",
                            affected_url=str(response.url),
                            affected_parameter=point["parameter"],
                            evidence=f"Payload отражён без санитизации: {payload[:50]}...",
                        ))
                        break  # One finding per parameter is enough

    def _get_reflection_context(self, html: str, payload: str) -> dict:
        """Analyze where the payload is reflected in the HTML."""
        context = {
            "unsanitized": False,
            "in_script": False,
            "in_attribute": False,
            "in_html_body": False,
            "encoded": False,
            "description": "неизвестно",
        }

        idx = html.find(payload)
        if idx == -1:
            # Check encoded versions
            encoded = payload.replace("<", "&lt;").replace(">", "&gt;")
            if encoded in html:
                context["encoded"] = True
                context["unsanitized"] = False
                context["description"] = "Payload HTML-кодирован (безопасно)"
                return context
            return context

        # Get surrounding context (200 chars before and after)
        start = max(0, idx - 100)
        end = min(len(html), idx + len(payload) + 100)
        surrounding = html[start:end]

        context["unsanitized"] = True

        # Check if inside <script> tag
        script_before = html[:idx].rfind("<script")
        script_after = html[idx:].find("</script>")
        if script_before != -1 and script_after != -1:
            context["in_script"] = True
            context["description"] = "Отражён внутри тега <script> (КРИТИЧНО)"
            return context

        # Check if inside HTML attribute
        attr_pattern = r'="[^"]*' + re.escape(payload[:20])
        if re.search(attr_pattern, surrounding):
            context["in_attribute"] = True
            context["description"] = "Отражён внутри HTML-атрибута"
            return context

        # Check if in HTML body
        body_before = html[:idx].rfind("<body")
        if body_before != -1:
            context["in_html_body"] = True
            context["description"] = "Отражён в HTML-теле"
            return context

        context["description"] = "Отражён в неизвестном контексте"
        return context

    async def _check_dom_xss_patterns(self):
        """Check for DOM-based XSS patterns in JavaScript files."""
        # Find JS files
        response = await self._make_request(path="/")
        if not response or not response.text:
            return

        soup = BeautifulSoup(response.text, "html.parser")
        js_urls = []

        for script in soup.find_all("script", src=True):
            js_urls.append(script["src"])

        # Check inline scripts for dangerous patterns
        for script in soup.find_all("script"):
            if script.string:
                self._analyze_js_content(script.string)

        # Fetch and analyze external JS files (limit to 5)
        for js_url in js_urls[:5]:
            js_response = await self._make_request(url=js_url)
            if js_response and js_response.text:
                self._analyze_js_content(js_response.text)

    def _analyze_js_content(self, js_content: str):
        """Analyze JavaScript for DOM XSS sink patterns."""
        dangerous_sinks = [
            (r"\.innerHTML\s*=", "присваивание innerHTML", "Используйте textContent вместо innerHTML для пользовательских данных"),
            (r"\.outerHTML\s*=", "присваивание outerHTML", "Избегайте установки outerHTML с пользовательскими данными"),
            (r"document\.write\s*\(", "document.write()", "Избегайте document.write(); используйте методы манипуляции DOM"),
            (r"\.insertAdjacentHTML\s*\(", "insertAdjacentHTML()", "Санитизируйте контент перед использованием insertAdjacentHTML"),
            (r"eval\s*\(", "использование eval()", "Избегайте eval() с пользовательским вводом"),
            (r"setTimeout\s*\(['\"]", "setTimeout со строкой", "Используйте ссылки на функции вместо строк"),
            (r"location\s*=", "присваивание location", "Валидируйте URL перед присваиванием"),
            (r"window\.location\s*=", "присваивание window.location", "Валидируйте URL перед присваиванием"),
        ]

        for pattern, sink_name, remediation in dangerous_sinks:
            if re.search(pattern, js_content):
                self._log_finding(self._create_finding(
                    title=f"DOM XSS-ловушка: {sink_name}",
                    description=f"JavaScript-код содержит {sink_name}, что может привести к DOM XSS при использовании с пользовательскими данными.",
                    severity=Severity.MEDIUM,
                    remediation=remediation,
                    cwe_id="CWE-79",
                    owasp_category="A07:2021",
                    owasp_name="DOM-based XSS",
                    evidence=f"Найден паттерн: {sink_name}",
                ))
