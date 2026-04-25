"""
SafeScan — SSL/TLS Module

Checks SSL/TLS configuration: protocols, ciphers, certificates.
"""

import asyncio
import ssl
from datetime import datetime, timezone
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class SSLTLSModule(ScanModule):
    """Module for checking SSL/TLS configuration."""

    async def execute(self) -> ScanResult:
        """Execute SSL/TLS assessment."""
        self.start_time = asyncio.get_event_loop().time()

        try:
            await self._check_certificate()
            await self._check_http_access()
            await self._check_hsts_on_https()
        except Exception as e:
            self._log_finding(self._create_finding(
                title="Ошибка проверки SSL/TLS",
                description=f"Ошибка при оценке SSL/TLS: {str(e)}",
                severity=Severity.HIGH,
                remediation="Убедитесь, что сервер поддерживает HTTPS.",
            ))

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="ssl_tls",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_certificate(self):
        """Check SSL certificate validity."""
        import socket
        loop = asyncio.get_event_loop()

        def get_cert():
            try:
                context = ssl.create_default_context()
                with context.wrap_socket(socket.socket(), server_hostname=self.domain) as sock:
                    sock.settimeout(10)
                    sock.connect((self.domain, 443))
                    cert = sock.getpeercert(binary_form=True)
                    verify_mode = context.verify_mode
                    return ssl.DER_cert_to_PEM_cert(cert), verify_mode
            except ssl.SSLError as e:
                return None, f"SSLError: {e}"
            except ConnectionRefusedError:
                return None, "Connection refused on port 443"
            except Exception as e:
                return None, str(e)

        try:
            pem_cert, error = await loop.run_in_executor(None, get_cert)

            if error and not pem_cert:
                self._log_finding(self._create_finding(
                    title="SSL-сертификат не найден",
                    description=f"Сервер не предоставляет SSL-сертификат на порту 443. Ошибка: {error}",
                    severity=Severity.CRITICAL,
                    remediation="Убедитесь, что сервер слуает порт 443 и настроен HTTPS. Установите действующий SSL-сертификат от доверенного центра сертификации.",
                    cvss_score=7.5,
                    cwe_id="CWE-295",
                    owasp_category="A02:2021",
                    evidence=f"Ошибка подключения: {error}",
                ))
                return

            # Parse expiry
            import OpenSSL.crypto
            x509 = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, pem_cert.encode())
            expiry_bytes = x509.get_notAfter()
            expiry_str = expiry_bytes.decode('utf-8')
            expiry = datetime.strptime(expiry_str, "%Y%m%d%H%M%SZ").replace(tzinfo=timezone.utc)
            days_left = (expiry - datetime.now(timezone.utc)).days

            if expiry < datetime.now(timezone.utc):
                self._log_finding(self._create_finding(
                    title="SSL-сертификат истёк",
                    description=f"Срок действия сертификата истёк {expiry.strftime('%Y-%m-%d')}.",
                    severity=Severity.CRITICAL,
                    remediation="Немедленно продлите SSL-сертификат.",
                    evidence=f"Истёк: {expiry.strftime('%Y-%m-%d')}",
                ))
            elif days_left < 30:
                self._log_finding(self._create_finding(
                    title="Срок SSL-сертификата скоро истекает",
                    description=f"Сертификат истекает через {days_left} дней.",
                    severity=Severity.MEDIUM,
                    remediation="Продлите SSL-сертификат до истечения срока.",
                    evidence=f"Осталось дней: {days_left}",
                ))

            # Check self-signed
            issuer = x509.get_issuer()
            subject = x509.get_subject()
            if issuer.CN == subject.CN:
                self._log_finding(self._create_finding(
                    title="Самоподписанный SSL-сертификат",
                    description="Сервер использует самоподписанный сертификат, который не доверяется браузерами.",
                    severity=Severity.MEDIUM,
                    remediation="Получите сертификат от доверенного центра сертификации (например, Let's Encrypt).",
                    evidence=f"Issuer CN = Subject CN = {subject.CN}",
                ))

        except Exception as e:
            self._log_finding(self._create_finding(
                title="Ошибка проверки сертификата",
                description=f"Ошибка при проверке сертификата: {str(e)}",
                severity=Severity.MEDIUM,
                remediation="Проверьте конфигурацию SSL.",
            ))

    async def _check_http_access(self):
        """Check if HTTP redirects to HTTPS properly."""
        try:
            resp = await self._make_request(
                url=f"http://{self.domain}/",
                follow_redirects=False,
                timeout=5.0,
            )
            if resp and resp.status_code == 200:
                # Check if HTTPS also works
                try:
                    https_resp = await self._make_request(
                        url=f"https://{self.domain}/",
                        follow_redirects=False,
                        timeout=5.0,
                    )
                except Exception:
                    https_resp = None

                if https_resp and https_resp.status_code in (200, 301, 302):
                    # Both work — warn about missing redirect
                    self._log_finding(self._create_finding(
                        title="HTTP не перенаправляет на HTTPS",
                        description=(
                            f"Сайт {self.domain} доступен по HTTP и HTTPS, "
                            f"но HTTP-запрос не перенаправляется автоматически на HTTPS. "
                            f"Это позволяет атакам типа downgrade."
                        ),
                        severity=Severity.MEDIUM,
                        remediation=(
                            "Настройте автоматическое перенаправление HTTP → HTTPS "
                            "в конфигурации веб-сервера."
                        ),
                        evidence=f"HTTP вернул: {resp.status_code}, HTTPS вернул: {https_resp.status_code}",
                    ))
                elif not https_resp or https_resp.status_code >= 400:
                    # HTTP works, HTTPS doesn't — real problem
                    self._log_finding(self._create_finding(
                        title="Сайт недоступен по HTTPS",
                        description=f"Сайт {self.domain} работает по HTTP, но не отвечает по HTTPS.",
                        severity=Severity.HIGH,
                        remediation="Включите HTTPS и перенаправляйте весь HTTP-трафик на HTTPS.",
                        cvss_score=7.5,
                        cwe_id="CWE-319",
                    ))
        except Exception:
            pass  # HTTP not accessible — probably redirects to HTTPS automatically

    async def _check_hsts_on_https(self):
        """Check HSTS header on HTTPS."""
        response = await self._make_request(path="/")
        if response:
            hsts = response.headers.get("strict-transport-security")
            if not hsts:
                self._log_finding(self._create_finding(
                    title="Отсутствует HSTS на HTTPS",
                    description="HTTPS-сайт не имеет заголовка HSTS.",
                    severity=Severity.MEDIUM,
                    remediation="Добавьте заголовок Strict-Transport-Security в HTTPS-ответы.",
                ))
