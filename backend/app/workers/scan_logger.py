"""
SafeScan — Scan Logger

Stores real-time scan logs in Redis for frontend polling.
Uses a shared Redis connection pool to avoid connection leaks.
"""

import json
import logging
import redis
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class _RedisPool:
    """Shared Redis connection pool for ScanLogger."""

    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> redis.Redis:
        """Get or create the shared Redis client."""
        if cls._client is None:
            url = settings.REDIS_URL
            logger.info(f"Initializing Redis connection to {url}")
            try:
                cls._client = redis.from_url(
                    url,
                    decode_responses=True,
                    socket_timeout=2,
                    socket_connect_timeout=2,
                    max_connections=20,
                )
                # Test connection
                cls._client.ping()
                logger.info("Redis connection established successfully")
            except redis.ConnectionError as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._client

    @classmethod
    def close(cls) -> None:
        """Close the shared Redis connection."""
        if cls._client:
            try:
                cls._client.close()
            except Exception:
                pass
            cls._client = None


class ScanLogger:
    """
    Stores scan logs in a Redis list for real-time retrieval.

    Each scan gets a Redis list: scan:logs:{scan_id}
    Entries are JSON strings with timestamp, level, module, and message.
    The list has a TTL of 24 hours to prevent memory leaks.
    """

    def __init__(self, scan_id: str):
        self.scan_id = scan_id
        self.redis_key = f"scan:logs:{scan_id}"

        try:
            self._client = _RedisPool.get_client()
        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            raise

        # Set TTL to 24 hours
        try:
            self._client.expire(self.redis_key, 86400)
        except Exception as e:
            logger.warning(f"Failed to set Redis TTL: {e}")

    def log(self, message: str, level: str = "INFO", module: Optional[str] = None):
        """Add a log entry."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "module": module,
            "message": message,
        }
        try:
            self._client.rpush(self.redis_key, json.dumps(entry))
            # Keep max 5000 log entries per scan
            self._client.ltrim(self.redis_key, -5000, -1)
            self._client.expire(self.redis_key, 86400)
        except Exception as e:
            logger.error(f"Failed to write log to Redis: {e}")

    def get_logs(self, offset: int = 0, limit: int = 500) -> list[dict]:
        """Retrieve log entries."""
        try:
            entries = self._client.lrange(self.redis_key, offset, offset + limit - 1)
            return [json.loads(e) for e in entries]
        except Exception as e:
            logger.error(f"Failed to read logs from Redis: {e}")
            return []

    def get_total_count(self) -> int:
        """Get total number of log entries."""
        try:
            return self._client.llen(self.redis_key)
        except Exception as e:
            logger.error(f"Failed to get log count from Redis: {e}")
            return 0

    def close(self):
        """No-op — connections are shared via pool. Call _RedisPool.close() on shutdown."""
        pass
