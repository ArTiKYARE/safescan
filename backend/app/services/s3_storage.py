"""
SafeScan — S3 Storage Service
"""

import io
from typing import Optional

import aioboto3

from app.core.config import settings


class S3Service:
    """Async S3-compatible storage service (MinIO, AWS S3, etc.)."""

    def __init__(self):
        self._session = aioboto3.Session()
        self._bucket = settings.S3_BUCKET
        self._endpoint = settings.S3_ENDPOINT_URL
        self._access_key = settings.S3_ACCESS_KEY
        self._secret_key = settings.S3_SECRET_KEY
        self._region = settings.S3_REGION

    async def _get_client(self):
        """Create an async S3 client."""
        client = await self._session.client(
            "s3",
            endpoint_url=self._endpoint,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        ).__aenter__()
        return client

    async def upload_file(self, key: str, content: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes to S3 and return the object key."""
        client = await self._get_client()
        try:
            await client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=content,
                ContentType=content_type,
            )
            return key
        finally:
            await client.close()

    async def download_file(self, key: str) -> Optional[bytes]:
        """Download file from S3."""
        client = await self._get_client()
        try:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            return await response["Body"].read()
        except client.exceptions.NoSuchKey:
            return None
        finally:
            await client.close()

    async def delete_file(self, key: str) -> bool:
        """Delete a file from S3."""
        client = await self._get_client()
        try:
            await client.delete_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False
        finally:
            await client.close()

    async def file_exists(self, key: str) -> bool:
        """Check if a file exists in S3."""
        client = await self._get_client()
        try:
            await client.head_object(Bucket=self._bucket, Key=key)
            return True
        except Exception:
            return False
        finally:
            await client.close()


# Singleton
s3_service = S3Service()
