"""
Simple in-memory rate limiter for public endpoints.
Prevents spam on booking/contact/intake forms.
"""
import time
from collections import defaultdict
from fastapi import HTTPException, Request


class RateLimiter:
    """Token-bucket-style rate limiter keyed by client IP."""

    def __init__(self, max_requests: int = 30, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, key: str):
        """Remove expired timestamps."""
        cutoff = time.time() - self.window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def check(self, request: Request):
        """Raise 429 if rate limit exceeded for the client IP."""
        client_ip = request.client.host if request.client else "unknown"
        self._cleanup(client_ip)

        if len(self._requests[client_ip]) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )
        self._requests[client_ip].append(time.time())


# Shared instance: 30 requests per minute per IP for public endpoints
public_rate_limiter = RateLimiter(max_requests=30, window_seconds=60)
