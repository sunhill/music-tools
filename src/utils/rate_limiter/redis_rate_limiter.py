import logging

import time
from typing import Optional
import redis

from utils.rate_limiter.rate_limiter_interface import RateLimiterInterface, RateLimiterConfig, RateLimitInfo

logger = logging.getLogger(__name__)


class RedisRateLimiter(RateLimiterInterface):
    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()
        self.redis = redis.from_url(
            self.config.redis_url, db=self.config.redis_db, decode_responses=True
        )
        self._init_bucket()

    def _init_bucket(self):
        """Initialize the token bucket if it doesn't exist."""
        if not self.redis.exists("spotify_rate_limit"):
            self.redis.set("spotify_rate_limit", self.config.burst_size)
            self.redis.set("spotify_rate_limit_reset", time.time() + 60)

    def acquire(self) -> bool:
        """
        Try to acquire a token from the bucket.
        Returns True if successful, False if rate limited.
        """
        current_time = time.time()
        reset_time = float(self.redis.get("spotify_rate_limit_reset"))

        # If we've passed the reset time, refill the bucket
        if current_time >= reset_time:
            self.redis.set("spotify_rate_limit", self.config.burst_size)
            self.redis.set("spotify_rate_limit_reset", current_time + 60)
            return True

        # Try to get a token
        remaining = self.redis.decr("spotify_rate_limit")
        if remaining < 0:
            # We're rate limited
            self.redis.incr("spotify_rate_limit")  # Put the token back
            return False

        return True

    def get_rate_limit_info(self) -> RateLimitInfo:
        """Get current rate limit information."""
        remaining = int(self.redis.get("spotify_rate_limit"))
        reset = float(self.redis.get("spotify_rate_limit_reset"))
        return RateLimitInfo(
            remaining=remaining, reset=reset, limit=self.config.burst_size
        )

    def wait_for_token(self) -> None:
        """Wait until a token is available."""
        while not self.acquire():
            time.sleep(0.1)  # Small sleep to prevent CPU spinning

    def get_retry_after(self) -> int:
        """Get the retry-after time in seconds."""
        return self.config.retry_after
