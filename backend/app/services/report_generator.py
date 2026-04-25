"""
SafeScan — Report Generator Service
"""

import json
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.scan import Scan
from app.models.vulnerability import Vulnerability
from app.models.domain import Domain
from app.services.s3_storage import s3_service


class ReportGeneratorService:
    """Generate scan reports in JSON, HTML, and PDF formats."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_json(self, scan: Scan) -> dict:
        """Generate a JSON report."""
        # Fetch vulnerabilities
        result = await self.db.execute(
            select(Vulnerability)
            .where(Vulnerability.scan_id == scan.id)
            .order_by(
                Vulnerability.severity.asc(),
                Vulnerability.created_at.desc(),
            )
        )
        vulnerabilities = result.scalars().all()

        # Fetch domain
        domain_result = await self.db.execute(
            select(Domain).where(Domain.id == scan.domain_id)
        )
        domain = domain_result.scalar_one_or_none()

        # Calculate duration
        duration = ""
        if scan.started_at and scan.completed_at:
            delta = scan.completed_at - scan.started_at
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        report = {
            "report": {
                "metadata": {
                    "scan_id": str(scan.id),
                    "domain": domain.domain if domain else "unknown",
                    "scan_date": scan.started_at.isoformat() if scan.started_at else None,
                    "scan_duration": duration,
                    "scanner_version": "1.0.0",
                    "modules_executed": len(scan.modules_enabled or []),
                    "modules_failed": 0,
                },
                "summary": {
                    "total_findings": scan.total_findings,
                    "critical": scan.critical_count,
                    "high": scan.high_count,
                    "medium": scan.medium_count,
                    "low": scan.low_count,
                    "info": scan.info_count,
                    "risk_score": scan.risk_score or 0,
                    "grade": scan.grade or "N/A",
                },
                "vulnerabilities": [
                    {
                        "id": str(v.id),
                        "module": v.module,
                        "title": v.title,
                        "description": v.description,
                        "severity": v.severity,
                        "cvss": {
                            "score": v.cvss_score,
                            "vector": v.cvss_vector,
                        } if v.cvss_score else None,
                        "affected": v.affected_url,
                        "evidence": v.evidence,
                        "remediation": v.remediation,
                        "cwe": v.cwe_id,
                        "owasp": v.owasp_category,
                        "references": [],
                    }
                    for v in vulnerabilities
                ],
                "compliance": {
                    "owasp_top_10": self._calculate_owasp_compliance(vulnerabilities),
                    "pci_dss": {
                        "compliant": scan.grade in ("A+", "A", "B") if scan.grade else False,
                        "failures": [],
                    },
                },
            },
        }
        return report

    async def generate_html(self, scan: Scan) -> str:
        """Generate an HTML report."""
        json_report = await self.generate_json(scan)
        report = json_report["report"]

        severity_colors = {
            "critical": "#dc2626",
            "high": "#ea580c",
            "medium": "#d97706",
            "low": "#2563eb",
            "info": "#6b7280",
        }

        vuln_rows = ""
        for v in report["vulnerabilities"]:
            color = severity_colors.get(v["severity"], "#6b7280")
            vuln_rows += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                    <span style="background: {color}; color: white; padding: 2px 8px;
                                 border-radius: 4px; font-size: 12px;">
                        {v['severity'].upper()}
                    </span>
                </td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{v['title']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{v['module']}</td>
                <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">
                    {v['cvss']['score'] if v['cvss'] else 'N/A'}
                </td>
            </tr>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>SafeScan Report - {report['metadata']['domain']}</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                       margin: 0; padding: 24px; color: #1f2937; }}
                .header {{ background: linear-gradient(135deg, #2563eb, #7c3aed);
                          color: white; padding: 32px; border-radius: 12px; margin-bottom: 24px; }}
                .summary {{ display: flex; gap: 16px; margin: 24px 0; flex-wrap: wrap; }}
                .summary-card {{ background: #f9fafb; padding: 16px; border-radius: 8px;
                                 min-width: 120px; text-align: center; }}
                .summary-card .number {{ font-size: 32px; font-weight: bold; }}
                .summary-card .label {{ color: #6b7280; font-size: 14px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 24px 0; }}
                th {{ background: #f3f4f6; text-align: left; padding: 12px 8px; }}
                .footer {{ margin-top: 48px; padding-top: 16px; border-top: 1px solid #e5e7eb;
                          color: #6b7280; font-size: 14px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🛡️ SafeScan Security Report</h1>
                <p>Domain: <strong>{report['metadata']['domain']}</strong></p>
                <p>Date: {report['metadata']['scan_date']}</p>
                <p>Grade: <strong style="font-size: 24px;">{report['summary']['grade']}</strong>
                   | Risk Score: <strong>{report['summary']['risk_score']}/10</strong></p>
            </div>

            <div class="summary">
                <div class="summary-card">
                    <div class="number">{report['summary']['total_findings']}</div>
                    <div class="label">Total Findings</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: #dc2626;">{report['summary']['critical']}</div>
                    <div class="label">Critical</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: #ea580c;">{report['summary']['high']}</div>
                    <div class="label">High</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: #d97706;">{report['summary']['medium']}</div>
                    <div class="label">Medium</div>
                </div>
                <div class="summary-card">
                    <div class="number" style="color: #2563eb;">{report['summary']['low']}</div>
                    <div class="label">Low</div>
                </div>
            </div>

            <h2>Vulnerabilities</h2>
            <table>
                <thead>
                    <tr>
                        <th>Severity</th>
                        <th>Title</th>
                        <th>Module</th>
                        <th>CVSS</th>
                    </tr>
                </thead>
                <tbody>
                    {vuln_rows if vuln_rows else '<tr><td colspan="4" style="padding: 24px; text-align: center; color: #6b7280;">No vulnerabilities found 🎉</td></tr>'}
                </tbody>
            </table>

            <div class="footer">
                <p>Generated by SafeScan v1.0.0 | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</p>
                <p>This report is for defensive security purposes only.</p>
            </div>
        </body>
        </html>
        """
        return html

    async def generate_pdf(self, scan: Scan) -> bytes:
        """Generate a PDF report using WeasyPrint."""
        html_content = await self.generate_html(scan)

        try:
            from weasyprint import HTML
            pdf_bytes = HTML(string=html_content).write_pdf()
            return pdf_bytes
        except Exception:
            # Fallback: return HTML if WeasyPrint fails
            return html_content.encode("utf-8")

    async def save_reports_to_s3(self, scan: Scan) -> dict:
        """Generate and upload all report formats to S3. Returns S3 keys."""
        import asyncio

        json_report = await self.generate_json(scan)
        json_bytes = json.dumps(json_report, indent=2, ensure_ascii=False).encode("utf-8")
        html_bytes = (await self.generate_html(scan)).encode("utf-8")
        pdf_bytes = await self.generate_pdf(scan)

        # Upload all formats in parallel
        keys = {
            "json": f"reports/{scan.id}/report.json",
            "html": f"reports/{scan.id}/report.html",
            "pdf": f"reports/{scan.id}/report.pdf",
        }

        json_key, html_key, pdf_key = await asyncio.gather(
            s3_service.upload_file(keys["json"], json_bytes, "application/json"),
            s3_service.upload_file(keys["html"], html_bytes, "text/html"),
            s3_service.upload_file(keys["pdf"], pdf_bytes, "application/pdf"),
        )

        # Update scan record with S3 paths
        scan.report_json_path = json_key
        scan.report_html_path = html_key
        scan.report_pdf_path = pdf_key

        return {
            "json_url": json_key,
            "html_url": html_key,
            "pdf_url": pdf_key,
        }

    def _calculate_owasp_compliance(
        self, vulnerabilities: list
    ) -> dict:
        """Calculate OWASP Top 10 compliance status."""
        owasp_categories = {
            "A01_broken_access_control": "FAIL",
            "A02_cryptographic_failures": "FAIL",
            "A03_injection": "PASS",
            "A04_insecure_design": "PASS",
            "A05_security_misconfiguration": "PASS",
            "A06_vulnerable_components": "PASS",
            "A07_auth_failures": "PASS",
            "A08_data_integrity": "PASS",
            "A09_logging_failures": "PASS",
            "A10_ssrf": "PASS",
        }

        owasp_mapping = {
            "injection": "A03_injection",
            "xss": "A03_injection",
            "ssrf_xxe_traversal": "A10_ssrf",
            "auth_sessions": "A07_auth_failures",
            "security_headers": "A05_security_misconfiguration",
            "ssl_tls": "A02_cryptographic_failures",
            "sca": "A06_vulnerable_components",
            "csrf_cors": "A01_broken_access_control",
        }

        for vuln in vulnerabilities:
            if vuln.false_positive or vuln.is_resolved:
                continue
            category = owasp_mapping.get(vuln.module)
            if category:
                owasp_categories[category] = "FAIL"

        return owasp_categories
