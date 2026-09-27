"""
Minimal in-memory rate limiter — no Redis dependency for something this
small. Fine for a single-process MVP; swap for Redis-backed limiting
(you already have Redis in docker-compose) before running multiple workers.
"""
import time
from collections import defaultdict
from fastapi import HTTPException, Request

_hits: dict[str, list[float]] = defaultdict(list)


def rate_limit(key_prefix: str, max_requests: int = 5, window_seconds: int = 60):
    def dependency(request: Request):
        key = f"{key_prefix}:{request.client.host}"
        now = time.time()
        _hits[key] = [t for t in _hits[key] if now - t < window_seconds]
        if len(_hits[key]) >= max_requests:
            raise HTTPException(status_code=429, detail="Too many attempts — try again shortly.")
        _hits[key].append(now)

    return dependency
