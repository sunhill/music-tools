import time
from threading import Lock

from black import Optional

from utils.rate_limiter.rate_limiter_interface import RateLimiterInterface, RateLimiterConfig


class InMemoryRateLimiter(RateLimiterInterface):
    def __init__(self, config: Optional[RateLimiterConfig] = None):
        self.config = config or RateLimiterConfig()
        self.rate = self.config.default_rate
        self.burst_size = self.config.burst_size
        self.tokens = self.burst_size
        self.last_refill = time.time()
        self.lock = Lock()

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst_size, self.tokens + int(elapsed * self.rate / 60))
        self.last_refill = now

    def acquire(self) -> bool:
        with self.lock:
            self._refill()
            if self.tokens > 0:
                self.tokens -= 1
                return True
            return False

    def wait_for_token(self) -> None:
        while not self.acquire():
            time.sleep(0.1)

    def get_rate_limit_info(self):
        with self.lock:
            self._refill()
            return {
                "remaining": self.tokens,
                "reset": self.last_refill + 60 / self.rate,
                "limit": self.burst_size
            }

    def get_retry_after(self) -> int:
        """Get the retry-after time in seconds."""
        return self.config.retry_after