"""
Rate limiting implementation for JIRA API calls.
"""
import time
import logging
from functools import wraps
from typing import Callable, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("simple_jira")

class RateLimiter:
    """Rate limiter implementation using token bucket algorithm."""
    
    def __init__(self, calls: int, period: int):
        """
        Initialize rate limiter.
        
        Args:
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        self.calls = calls
        self.period = period
        self.tokens = calls
        self.last_check = datetime.now()
    
    def _add_tokens(self) -> None:
        """Add tokens based on time elapsed."""
        now = datetime.now()
        time_passed = now - self.last_check
        self.tokens = min(
            self.calls,
            self.tokens + time_passed.total_seconds() * (self.calls / self.period)
        )
        self.last_check = now

    def acquire(self) -> float:
        """
        Acquire a token. Returns the time to wait if no tokens are available.
        """
        self._add_tokens()
        if self.tokens >= 1:
            self.tokens -= 1
            return 0.0
        
        # Calculate wait time
        wait_time = (self.period / self.calls) * (1 - self.tokens)
        return wait_time

def rate_limited(calls: int, period: int) -> Callable:
    """
    Decorator for rate limiting functions.
    
    Args:
        calls: Number of calls allowed per period
        period: Time period in seconds
    """
    limiter = RateLimiter(calls, period)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            wait_time = limiter.acquire()
            if wait_time > 0:
                logger.info(f"Rate limit reached. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
            return func(*args, **kwargs)
        return wrapper
    return decorator 