"""
SafeScan — Domain Verification Service
"""

import asyncio
import httpx
import dns.resolver
import logging
from typing import Optional, List

from app.models.domain import Domain

logger = logging.getLogger(__name__)


class DomainVerificationService:
    """Service for verifying domain ownership via DNS, File, or Email methods."""

    # Константы для верификации
    DNS_RECORD_NAME = "_safescan-verify"
    FILE_VERIFICATION_PATH = "/.well-known/safescan-verify.txt"
    EMAIL_VERIFICATION_ADDRESSES = ["admin", "webmaster", "hostmaster"]
    DNS_TIMEOUT = 10.0
    HTTP_TIMEOUT = 10.0
    MAX_REDIRECTS = 3
    # 👇 Публичные DNS-серверы для обхода кэша Docker
    PUBLIC_DNS_SERVERS = ["8.8.8.8", "1.1.1.1"]

    async def verify(self, domain: Domain) -> bool:
        """
        Run verification based on configured method.
        Returns True ONLY if token matches exactly.
        
        Args:
            domain: Domain model with verification_token and verification_method
            
        Returns:
            bool: True if verification successful, False otherwise
        """
        if not domain.verification_token:
            logger.warning(f"Domain {domain.domain} has no verification token configured")
            return False
            
        if domain.verification_method == "dns":
            result = await self.check_dns(
                domain.domain, 
                expected_token=domain.verification_token
            )
            return result.get("verified", False)
            
        elif domain.verification_method == "file":
            result = await self.check_file(
                domain.domain,
                expected_token=domain.verification_token
            )
            return result.get("verified", False)
            
        elif domain.verification_method == "email":
            # Email verification is confirmed when user clicks the link
            return bool(domain.is_verified)
            
        logger.warning(f"Unknown verification method for domain {domain.domain}: {domain.verification_method}")
        return False

    async def check_dns(
        self,
        domain: str,
        expected_token: Optional[str] = None,
    ) -> dict:
        """
        Check DNS TXT record for domain verification.
        
        Looks for _safescan-verify.<domain> TXT record.
        Verification passes ONLY if the exact token is found.
        
        Args:
            domain: Domain name to check (e.g., "example.com")
            expected_token: Token to match against (optional for discovery mode)
            
        Returns:
            dict: Verification result with details
        """
        record_name = f"{self.DNS_RECORD_NAME}.{domain}"
        result = {
            "domain": domain,
            "record_name": record_name,
            "verified": False,
            "records": [],
            "error": None,
            "method": "dns"
        }

        try:
            logger.info(f"Checking DNS TXT record: {record_name}")
            
            # 👇 Создаём резолвер с явными публичными DNS-серверами
            resolver = dns.resolver.Resolver()
            resolver.nameservers = self.PUBLIC_DNS_SERVERS  # ['8.8.8.8', '1.1.1.1']
            resolver.lifetime = self.DNS_TIMEOUT
            resolver.timeout = 5.0  # Таймаут на один запрос
            
            # Resolve TXT records
            answers = resolver.resolve(record_name, "TXT")
            
            # Parse TXT records — handle multi-part records
            records: List[str] = []
            for rdata in answers:
                txt = rdata.to_text()
                # Remove surrounding quotes and join split parts
                # TXT records can be split: "part1" "part2" -> "part1part2"
                txt = txt.strip('"').replace('" "', '').replace('"', '')
                if txt:  # Skip empty records
                    records.append(txt)
            
            result["records"] = records
            logger.info(f"Found {len(records)} TXT record(s) for {record_name}: {records[:3]}")

            # Strict token matching ONLY — exact match required
            if expected_token:
                if expected_token in records:
                    result["verified"] = True
                    logger.info(f"✅ DNS verification SUCCESS for {domain}: token matched")
                else:
                    logger.warning(
                        f"❌ DNS verification FAILED for {domain}: "
                        f"expected '{expected_token[:20]}...', got {records}"
                    )
                    result["error"] = "Token mismatch"
            else:
                # Discovery mode — just return found records
                logger.info(f"🔍 DNS discovery mode for {domain}: found {len(records)} record(s)")

        except dns.resolver.NoAnswer:
            result["error"] = "No TXT record found"
            logger.warning(f"DNS NoAnswer for {record_name}")
            
        except dns.resolver.NXDOMAIN:
            result["error"] = "Domain does not exist"
            logger.warning(f"DNS NXDOMAIN for {record_name}")
            
        except dns.resolver.NoNameservers:
            result["error"] = "No nameservers available"
            logger.error(f"DNS NoNameservers for {record_name}")
            
        except dns.resolver.Timeout:
            result["error"] = "DNS query timed out"
            logger.warning(f"DNS timeout for {record_name}")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            result["error"] = error_msg
            logger.error(f"DNS check error for {record_name}: {error_msg}")

        return result

    async def check_file(
        self,
        domain: str,
        expected_token: Optional[str] = None,
    ) -> dict:
        """
        Check verification file at /.well-known/safescan-verify.txt
        
        Verification passes ONLY if the file content matches the expected token exactly.
        
        Args:
            domain: Domain name to check (e.g., "example.com")
            expected_token: Token to match against (optional for discovery mode)
            
        Returns:
            dict: Verification result with details
        """
        # Try HTTPS first, then HTTP as fallback
        urls = [
            f"https://{domain}{self.FILE_VERIFICATION_PATH}",
            f"http://{domain}{self.FILE_VERIFICATION_PATH}",
        ]
        
        result = {
            "domain": domain,
            "url": urls[0],
            "verified": False,
            "content": None,
            "error": None,
            "method": "file"
        }

        for url in urls:
            try:
                logger.info(f"Checking verification file: {url}")
                
                async with httpx.AsyncClient(
                    verify=True,
                    timeout=self.HTTP_TIMEOUT,
                    follow_redirects=True,
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                    headers={
                        "User-Agent": "SafeScan-Verifier/1.0 (+https://safescanget.ru)",
                        "Accept": "text/plain",
                    }
                ) as client:
                    response = await client.get(url)
                    
                    if response.status_code == 200:
                        content = response.text.strip()
                        result["content"] = content
                        result["url"] = url
                        
                        logger.info(f"File check for {domain}: got {len(content)} chars from {url}")
                        
                        if expected_token:
                            if content == expected_token:
                                result["verified"] = True
                                logger.info(f"✅ File verification SUCCESS for {domain}: token matched")
                                return result
                            else:
                                logger.warning(
                                    f"❌ File verification FAILED for {domain}: "
                                    f"expected len={len(expected_token)}, got len={len(content)}"
                                )
                                result["error"] = f"Token mismatch (expected {len(expected_token)} chars, got {len(content)} chars)"
                        else:
                            logger.info(f"🔍 File discovery mode for {domain}: found file with {len(content)} chars")
                        
                        break
                        
                    elif response.status_code == 404:
                        result["error"] = "Verification file not found (404)"
                        logger.debug(f"File not found at {url} (404)")
                        
                    elif response.status_code == 403:
                        result["error"] = "Access forbidden (403)"
                        logger.warning(f"File access forbidden at {url} (403)")
                        break
                        
                    else:
                        result["error"] = f"HTTP {response.status_code}"
                        logger.warning(f"File check got HTTP {response.status_code} from {url}")
                        
            except httpx.ConnectError:
                result["error"] = f"Connection failed to {url}"
                logger.debug(f"Connection failed to {url}")
                
            except httpx.TimeoutException:
                result["error"] = f"Request timed out for {url}"
                logger.warning(f"Timeout checking {url}")
                
            except httpx.SSLError as e:
                logger.warning(f"SSL error for {url}: {e}")
                if url.startswith("https://"):
                    continue
                result["error"] = f"SSL error: {str(e)}"
                break
                
            except httpx.HTTPStatusError as e:
                result["error"] = f"HTTP error: {e.response.status_code}"
                logger.warning(f"HTTP status error for {url}: {e.response.status_code}")
                break
                
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                result["error"] = f"Unexpected error: {error_msg}"
                logger.error(f"File check error for {domain} at {url}: {error_msg}")
                break

        if not result["verified"] and not result["error"]:
            result["error"] = "Verification file not accessible"
            
        return result

    async def check_email(self, domain: Domain, token: Optional[str] = None) -> dict:
        """
        Check if email verification token is valid.
        """
        result = {
            "domain": domain.domain,
            "verified": domain.is_verified,
            "method": "email",
            "error": None,
            "email_addresses": [
                f"{addr}@{domain.domain}" for addr in self.EMAIL_VERIFICATION_ADDRESSES
            ]
        }
        
        if token and domain.api_verification_token:
            if len(token) < 32:
                result["error"] = "Invalid token format"
                result["verified"] = False
            elif token == domain.api_verification_token:
                result["verified"] = True
                logger.info(f"✅ Email verification token matched for {domain.domain}")
            else:
                result["error"] = "Token mismatch"
                result["verified"] = False
                logger.warning(f"❌ Email token mismatch for {domain.domain}")
        
        return result

    @staticmethod
    def generate_verification_token() -> str:
        """Generate a cryptographically secure verification token."""
        import secrets
        return secrets.token_hex(16)

    @staticmethod
    def get_dns_instructions(domain: str, token: str) -> dict:
        """Generate DNS verification instructions for the user."""
        record_name = f"{DomainVerificationService.DNS_RECORD_NAME}.{domain}"
        
        return {
            "method": "dns",
            "record_type": "TXT",
            "record_name": record_name,
            "record_value": token,
            "instructions": [
                f"Log in to your DNS provider for {domain}",
                f"Add a new TXT record with name: {record_name}",
                f"Set the value to: {token}",
                "Save changes and wait for DNS propagation (up to 24 hours, usually 5-10 min)",
                f"Use the verification endpoint to check status"
            ],
            "example_commands": {
                "dig": f"dig TXT {record_name} +short",
                "nslookup": f"nslookup -type=TXT {record_name}"
            }
        }

    @staticmethod
    def get_file_instructions(domain: str, token: str) -> dict:
        """Generate file verification instructions for the user."""
        file_path = DomainVerificationService.FILE_VERIFICATION_PATH
        full_url = f"https://{domain}{file_path}"
        
        return {
            "method": "file",
            "file_path": file_path,
            "file_content": token,
            "full_url": full_url,
            "instructions": [
                f"Create a file at: {file_path}",
                f"File content must be exactly: {token}",
                f"Ensure the file is publicly accessible at: {full_url}",
                "Use the verification endpoint to check status"
            ],
            "example_commands": {
                "curl": f"curl -I {full_url}",
                "wget": f"wget -qO- {full_url}"
            }
        }

    @staticmethod
    def get_email_instructions(domain: str) -> dict:
        """Generate email verification instructions for the user."""
        email_addresses = [
            f"{addr}@{domain}" for addr in DomainVerificationService.EMAIL_VERIFICATION_ADDRESSES
        ]
        
        return {
            "method": "email",
            "email_addresses": email_addresses,
            "instructions": [
                f"Check inbox for one of: {', '.join(email_addresses)}",
                "Look for email from noreply@safescanget.ru",
                "Click the verification link in the email",
                "Link expires in 24 hours"
            ]
        }