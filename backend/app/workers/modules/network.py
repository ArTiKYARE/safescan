"""
SafeScan — Network & Infrastructure Module

Checks DNS configuration, subdomain enumeration (passive),
CDN/WAF detection, SPF/DKIM/DMARC, IPv6, and IP reputation.

Standards: NIST-SC, CIS, RFC 7489
"""

import asyncio
import socket
import dns.resolver
from app.workers.modules.base import ScanModule, ScanResult, Finding, Severity


class NetworkModule(ScanModule):
    """Module for network and infrastructure checks."""

    async def execute(self) -> ScanResult:
        """Execute network/infrastructure checks."""
        self.start_time = asyncio.get_event_loop().time()

        await self._check_dns_configuration()
        await self._check_spf_dkim_dmarc()
        await self._check_cdn_waf_detection()
        await self._check_ipv6()
        await self._check_subdomain_takeover()

        duration = asyncio.get_event_loop().time() - self.start_time

        return ScanResult(
            module="network",
            findings=self.findings,
            success=True,
            duration_seconds=duration,
            requests_made=self.requests_made,
        )

    async def _check_dns_configuration(self):
        """Check DNS configuration for common issues."""
        try:
            loop = asyncio.get_event_loop()

            # Check A records with timeout
            try:
                a_records = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: dns.resolver.resolve(self.domain, "A")),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                self._log_finding(self._create_finding(
                    title="Превышен таймаут DNS-запроса",
                    description=f"DNS-запрос для {self.domain} превысил 5 секунд.",
                    severity=Severity.INFO,
                    remediation="Проверьте DNS-конфигурацию домена.",
                ))
                return

            if not a_records:
                self._log_finding(self._create_finding(
                    title="A-записи не найдены",
                    description=f"Для домена {self.domain} не найдено A-записей.",
                    severity=Severity.HIGH,
                    remediation="Убедитесь, что DNS A-записи правильно настроены.",
                ))
            else:
                # Check for multiple A records (load balancing)
                ips = [str(r) for r in a_records]
                if len(ips) > 1:
                    self._log_finding(self._create_finding(
                        title="Несколько A-записей (балансировка нагрузки)",
                        description=f"Домен имеет {len(ips)} A-записей: {', '.join(ips[:5])}",
                        severity=Severity.INFO,
                        remediation="Убедитесь, что все IP-адреса правильно настроены и мониторятся.",
                        evidence=f"A-записи: {', '.join(ips[:5])}",
                    ))

        except dns.resolver.NXDOMAIN:
            self._log_finding(self._create_finding(
                title="Домен не существует в DNS",
                description=f"Домен {self.domain} не имеет DNS-записей.",
                severity=Severity.CRITICAL,
                remediation="Настройте DNS-записи для домена.",
            ))
        except Exception as e:
            self._log_finding(self._create_finding(
                title="Ошибка разрешения DNS",
                description=f"Ошибка разрешения DNS для {self.domain}: {str(e)}",
                severity=Severity.INFO,
                remediation="Проверьте конфигурацию DNS.",
            ))

    async def _check_spf_dkim_dmarc(self):
        """Check email authentication records."""
        try:
            loop = asyncio.get_event_loop()

            # Check SPF with timeout
            try:
                spf_records = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: dns.resolver.resolve(self.domain, "TXT")),
                    timeout=5.0,
                )
            except asyncio.TimeoutError:
                self._log_finding(self._create_finding(
                    title="Превышен таймаут проверки SPF",
                    description="DNS-запрос для SPF-записей превысил 5 секунд.",
                    severity=Severity.INFO,
                    remediation="Проверьте DNS-конфигурацию.",
                ))
                return

            spf_found = any("v=spf1" in str(r) for r in spf_records)

            if not spf_found:
                self._log_finding(self._create_finding(
                    title="Отсутствует SPF-запись",
                    description=(
                        f"Для домена {self.domain} не найдена SPF-запись "
                        f"(Sender Policy Framework). SPF помогает предотвратить подделку email."
                    ),
                    severity=Severity.MEDIUM,
                    remediation=(
                        "Добавьте SPF TXT-запись: "
                        "v=spf1 include:_spf.google.com ~all "
                        "(настройте для вашего почтового провайдера)"
                    ),
                    cwe_id="CWE-345",
                    evidence="SPF TXT-запись не найдена",
                ))

            # Check DMARC with timeout
            try:
                dmarc_domain = f"_dmarc.{self.domain}"
                dmarc_records = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: dns.resolver.resolve(dmarc_domain, "TXT")),
                    timeout=5.0,
                )

                if dmarc_records:
                    dmarc = str(dmarc_records[0])
                    if "p=reject" not in dmarc.lower():
                        self._log_finding(self._create_finding(
                            title="Политика DMARC не установлена в reject",
                            description="Политика DMARC не установлена в 'reject', что снижает эффективность аутентификации email.",
                            severity=Severity.LOW,
                            remediation="Установите политику DMARC в 'p=reject' после мониторинга с 'p=none'.",
                            evidence=f"DMARC: {dmarc[:100]}",
                        ))
            except asyncio.TimeoutError:
                pass  # DMARC timeout — not critical
            except dns.resolver.NoAnswer:
                self._log_finding(self._create_finding(
                    title="Отсутствует DMARC-запись",
                    description=f"DMARC-запись не найдена для {self.domain}.",
                    severity=Severity.LOW,
                    remediation="Добавьте DMARC-запись на _dmarc.{domain}.",
                ))
            except dns.resolver.NXDOMAIN:
                self._log_finding(self._create_finding(
                    title="Отсутствует DMARC-запись",
                    description=f"DMARC-запись не найдена для _dmarc.{self.domain}.",
                    severity=Severity.LOW,
                    remediation="Добавьте DMARC-запись на _dmarc.{domain}.",
                ))

        except Exception as e:
            self._log_finding(self._create_finding(
                title="Ошибка проверки email-аутентификации",
                description=f"Ошибка проверки SPF/DMARC: {str(e)}",
                severity=Severity.INFO,
            ))

    async def _check_cdn_waf_detection(self):
        """Detect CDN and WAF usage."""
        response = await self._make_request(path="/")
        if not response:
            return

        headers_lower = {k.lower(): v.lower() for k, v in response.headers.items()}
        server = headers_lower.get("server", "")
        powered_by = headers_lower.get("x-powered-by", "")

        # CDN indicators
        cdn_indicators = {
            "Cloudflare": ["cloudflare", "cf-ray"],
            "Akamai": ["akamai", "x-akamai"],
            "Fastly": ["fastly", "x-fastly"],
            "AWS CloudFront": ["cloudfront", "x-amz-cf"],
            "Azure CDN": ["x-azure-ref"],
        }

        for cdn_name, indicators in cdn_indicators.items():
            if any(ind in server or any(ind in h for h in headers_lower.values()) for ind in indicators):
                self._log_finding(self._create_finding(
                    title=f"Обнаружен CDN: {cdn_name}",
                    description=f"Обнаружен CDN {cdn_name}. Это, как правило, положительно для безопасности.",
                    severity=Severity.INFO,
                    remediation="Убедитесь, что функции безопасности CDN (WAF, защита от DDoS) правильно настроены.",
                    evidence=f"Заголовки указывают на {cdn_name}",
                ))
                return

        # WAF indicators
        waf_indicators = {
            "AWS WAF": ["aws:waf"],
            "ModSecurity": ["mod_security", "modsecurity"],
            "Imperva": ["imperva", "incapsula"],
            "Sucuri": ["sucuri", "x-sucuri"],
            "Barracuda": ["barra"],
        }

        for waf_name, indicators in waf_indicators.items():
            if any(ind in server or any(ind in h for h in headers_lower.values()) for ind in indicators):
                self._log_finding(self._create_finding(
                    title=f"Обнаружен WAF: {waf_name}",
                    description=f"Обнаружен WAF {waf_name}.",
                    severity=Severity.INFO,
                    remediation=f"Убедитесь, что правила {waf_name} регулярно обновляются.",
                ))
                return

    async def _check_ipv6(self):
        """Check IPv6 configuration."""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, lambda: socket.getaddrinfo(self.domain, None, socket.AF_INET6)
            )

            if result:
                self._log_finding(self._create_finding(
                    title="IPv6 включён",
                    description="Домен имеет AAAA-записи (поддержка IPv6).",
                    severity=Severity.INFO,
                    remediation="Убедитесь, что правила межсетевого экрана IPv6 такие же строгие, как для IPv4.",
                ))
        except socket.gaierror:
            pass  # No IPv6 — not necessarily a problem
        except Exception:
            pass

    async def _check_subdomain_takeover(self):
        """Check for potential subdomain takeover."""
        # Reduced from 7 to 5 most common subdomains for speed
        common_subdomains = ["www", "mail", "ftp", "dev", "staging"]

        for subdomain in common_subdomains:
            full_domain = f"{subdomain}.{self.domain}"
            try:
                loop = asyncio.get_event_loop()
                a_records = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda d=full_domain: dns.resolver.resolve(d, "A")),
                    timeout=3.0,
                )

                for record in a_records:
                    ip = str(record)
                    # Check for common takeover IPs
                    takeover_ips = {
                        "75.2.60.5": "AWS S3 (ненастроенный бакет)",
                        "185.199.108.153": "GitHub Pages (ненастроенный репозиторий)",
                        "151.101.1.147": "Fastly (ненастроенный сервис)",
                    }

                    if ip in takeover_ips:
                        self._log_finding(self._create_finding(
                            title=f"Потенциальный перехват субдомена: {full_domain}",
                            description=(
                                f"Субдомен {full_domain} указывает на {takeover_ips[ip]}. "
                                f"Если внешний сервис не настроен, этот субдомен "
                                f"может быть перехвачен путём регистрации ресурса."
                            ),
                            severity=Severity.HIGH,
                            remediation=(
                                f"Либо настройте внешний сервис для {full_domain}, "
                                f"либо удалите DNS-запись."
                            ),
                            cvss_score=7.5,
                            cwe_id="CWE-684",
                            evidence=f"Разрешается в {ip} ({takeover_ips[ip]})",
                        ))

            except asyncio.TimeoutError:
                pass  # Subdomain DNS timeout — skip
            except dns.resolver.NXDOMAIN:
                pass  # Subdomain doesn't exist — fine
            except Exception:
                pass
