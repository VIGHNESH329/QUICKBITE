import time
from typing import Dict, List
from fastapi import HTTPException, status, Request
from app.core.config import settings

class SlidingWindowRateLimiter:
    """In-memory rate limiter tracking timestamps per client IP."""
    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests_map: Dict[str, List[float]] = {}

    def check(self, client_ip: str) -> None:
        now = time.time()
        timestamps = self.requests_map.get(client_ip, [])
        # Evict timestamps outside the sliding window
        valid_timestamps = [t for t in timestamps if now - t < self.window_seconds]
        
        if len(valid_timestamps) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - valid_timestamps[0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Too many login attempts. Please retry in {max(1, retry_after)} seconds.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
            
        valid_timestamps.append(now)
        self.requests_map[client_ip] = valid_timestamps

login_rate_limiter = SlidingWindowRateLimiter(
    max_requests=settings.MAX_LOGIN_ATTEMPTS_PER_MIN,
    window_seconds=60
)
