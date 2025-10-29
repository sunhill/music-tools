# Redis Configuration and Usage

This document explains how Redis is used in the Spotify Export project for rate limiting.

## Overview

Redis is used to implement a distributed rate limiting system that helps manage API requests to Spotify. The rate limiter uses a token bucket algorithm to ensure we don't exceed Spotify's API rate limits while allowing for efficient request handling.

## Prerequisites

1. Redis server installed and running
2. Redis Python client installed (included in requirements.txt)

## Installation

### macOS
```bash
# Install Redis using Homebrew
brew install redis

# Start Redis service
brew services start redis
```

### Linux (Ubuntu/Debian)
```bash
# Install Redis
sudo apt-get update
sudo apt-get install redis-server

# Start Redis service
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### Windows
1. Download Redis for Windows from https://github.com/microsoftarchive/redis/releases
2. Run the installer
3. Redis service should start automatically

## Configuration

Redis connection settings can be configured through environment variables:

```bash
# Default Redis URL (if not set)
export REDIS_URL="redis://localhost:6379"

# Optional: Set Redis database number (default: 0)
export REDIS_DB=0
```

## Rate Limiter Settings

The rate limiter is configured with the following default settings:

- Default rate: 30 requests per minute (Spotify's default rate limit)
- Burst size: 5 requests
- Retry after: 30 seconds

These settings can be modified in the `RateLimiterConfig` class:

```python
rate_limiter_config = RateLimiterConfig(
    redis_url=os.getenv("REDIS_URL", "redis://localhost:6379"),
    default_rate=30,  # requests per minute
    burst_size=5,     # maximum burst of requests
    retry_after=30    # seconds to wait when rate limited
)
```

## How It Works

1. **Token Bucket Algorithm**:
   - Each minute, the bucket is filled with tokens equal to the rate limit
   - Each API request consumes one token
   - If no tokens are available, requests are queued

2. **Distributed Rate Limiting**:
   - Redis stores the rate limiting state
   - Multiple instances of the application can share the same rate limit
   - Rate limiting persists between application restarts

3. **Error Handling**:
   - If Redis is unavailable, the rate limiter will fall back to a simple sleep-based approach
   - Rate limit information is available through the `get_rate_limit_info()` method

## Monitoring

You can monitor the rate limiter's state using Redis CLI:

```bash
# Connect to Redis CLI
redis-cli

# Check current rate limit tokens
GET spotify_rate_limit

# Check reset time
GET spotify_rate_limit_reset
```

## Troubleshooting

1. **Redis Connection Issues**:
   - Check if Redis service is running
   - Verify Redis URL and port
   - Check Redis logs for errors

2. **Rate Limiting Issues**:
   - Monitor rate limit tokens in Redis
   - Check application logs for rate limit warnings
   - Verify rate limit settings match Spotify's limits

## Security Considerations

1. **Redis Security**:
   - Use password protection for Redis
   - Limit Redis access to trusted networks
   - Keep Redis updated with security patches

2. **Rate Limiter Security**:
   - Rate limits are per application, not per user
   - Consider implementing per-user rate limiting if needed

## Development

When developing locally:

1. Start Redis server
2. Set environment variables if needed
3. Run the application
4. Monitor Redis for rate limiting behavior

## Production Deployment

For production:

1. Use a managed Redis service or dedicated Redis server
2. Configure proper security settings
3. Set up monitoring and alerts
4. Consider using Redis Sentinel for high availability 