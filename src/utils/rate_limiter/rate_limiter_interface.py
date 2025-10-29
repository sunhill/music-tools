from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class RateLimitInfo(BaseModel):
    remaining: int
    reset: float
    limit: int

class RateLimiterConfig(BaseSettings):
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0
    default_rate: int = 30  # requests per minute
    burst_size: int = 5     # maximum burst of requests
    retry_after: int = 30   # seconds to wait when rate limited


class RateLimiterInterface(ABC):
    @abstractmethod
    def acquire(self) -> bool:
        pass

    @abstractmethod
    def get_rate_limit_info(self) -> RateLimitInfo:
        pass

    @abstractmethod
    def wait_for_token(self) -> None:
        pass

    @abstractmethod
    def get_retry_after(self) -> int:
        pass