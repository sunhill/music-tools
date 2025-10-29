import asyncio
import logging
from time import time
from redis_rate_limiter import RedisRateLimiter, RateLimiterConfig

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_rate_limiter():
    # Initialize rate limiter with test configuration
    config = RateLimiterConfig(
        default_rate=30,  # 30 requests per minute
        burst_size=5,     # Allow bursts of 5 requests
        retry_after=30    # 30 seconds retry after
    )
    rate_limiter = RedisRateLimiter(config)
    
    logger.info("Starting rate limiter test...")
    start_time = time()
    
    # Test making multiple requests
    for i in range(10):  # Try to make 10 requests
        logger.info(f"Attempting request {i+1}")
        
        # Wait for rate limit token
        rate_limiter.wait_for_token()
        
        # Get current rate limit info
        info = rate_limiter.get_rate_limit_info()
        logger.info(f"Rate limit info - Remaining: {info.remaining}, Reset: {info.reset}")
        
        # Simulate API request
        logger.info(f"Making request {i+1}")
        await asyncio.sleep(0.1)  # Simulate request processing
        
    end_time = time()
    duration = end_time - start_time
    logger.info(f"Test completed in {duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(test_rate_limiter()) 