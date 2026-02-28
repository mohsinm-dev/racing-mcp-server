"""
Racing API HTTP client.

Handles:
- HTTP Basic Auth
- Automatic rate limiting (5 req/sec, 1 req/sec for static endpoints)
- TTL-based caching per endpoint type
- Clean error handling and response normalization
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import Any

import httpx
from cachetools import TTLCache

from .config import config

logger = logging.getLogger(__name__)

# ── Caches ──────────────────────────────────────────────────────────────────────
# Separate caches per TTL profile
_cache_static: TTLCache = TTLCache(maxsize=50, ttl=config.cache_ttl_static)
_cache_racecards: TTLCache = TTLCache(maxsize=200, ttl=config.cache_ttl_racecards)
_cache_results: TTLCache = TTLCache(maxsize=500, ttl=config.cache_ttl_results)
_cache_analysis: TTLCache = TTLCache(maxsize=1000, ttl=config.cache_ttl_analysis)
_cache_search: TTLCache = TTLCache(maxsize=2000, ttl=config.cache_ttl_search)


def _cache_key(url: str, params: dict) -> str:
    """Generate a stable cache key from URL + params."""
    raw = url + json.dumps(params, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def _select_cache(url: str) -> TTLCache:
    """Pick the right cache bucket based on the endpoint."""
    if "/courses" in url or "/regions" in url:
        return _cache_static
    if "/racecards" in url or "/odds" in url:
        return _cache_racecards
    if "/results" in url and "/analysis" not in url:
        return _cache_results
    if "/analysis" in url:
        return _cache_analysis
    if "/search" in url:
        return _cache_search
    return _cache_analysis  # Default to medium-TTL cache


# ── Rate limiter ────────────────────────────────────────────────────────────────

class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float, per: float = 1.0):
        self.rate = rate
        self.per = per
        self._allowance = rate
        self._last_check = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_check
            self._last_check = now
            self._allowance += elapsed * (self.rate / self.per)

            if self._allowance > self.rate:
                self._allowance = self.rate

            if self._allowance < 1.0:
                sleep_time = (1.0 - self._allowance) / (self.rate / self.per)
                await asyncio.sleep(sleep_time)
                self._allowance = 0.0
            else:
                self._allowance -= 1.0


# Two rate limiters matching The Racing API's documented limits
_limiter_general = RateLimiter(rate=5.0)   # 5 req/sec
_limiter_static = RateLimiter(rate=1.0)    # 1 req/sec for courses/regions


# ── Client ──────────────────────────────────────────────────────────────────────

class RacingAPIClient:
    """Async client for The Racing API with caching and rate limiting."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=config.base_url,
                auth=(config.username, config.password),
                timeout=30.0,
                headers={"Accept": "application/json"},
            )
        return self._client

    _MAX_RETRIES = 3
    _BACKOFF_BASE = 1.0  # seconds

    async def get(self, path: str, params: dict | None = None) -> dict | list:
        """Make a GET request with caching, rate limiting, and retry on 429."""
        params = {k: v for k, v in (params or {}).items() if v is not None}

        # Check cache
        cache = _select_cache(path)
        key = _cache_key(path, params)
        if key in cache:
            logger.debug(f"Cache HIT: {path}")
            return cache[key]

        # Apply rate limiting
        is_static = "/courses" in path or "/regions" in path
        limiter = _limiter_static if is_static else _limiter_general

        last_error: Exception | None = None
        for attempt in range(self._MAX_RETRIES):
            await limiter.acquire()

            client = await self._get_client()
            logger.info(f"API request: {path} params={params}")

            try:
                response = await client.get(path, params=params)
                response.raise_for_status()
                data = response.json()
                cache[key] = data
                return data

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise PermissionError(
                        "Invalid Racing API credentials. Check your username and password."
                    )
                elif e.response.status_code == 403:
                    raise PermissionError(
                        f"Your subscription plan does not include access to this endpoint: "
                        f"{path}. Consider upgrading to Standard or Pro plan."
                    )
                elif e.response.status_code == 404:
                    logger.info(f"404 Not Found: {path}")
                    return {"_not_found": True, "message": f"No data found for {path}"}
                elif e.response.status_code == 429:
                    last_error = e
                    wait = self._BACKOFF_BASE * (2 ** attempt)
                    logger.warning(
                        f"Rate limited (429), retrying in {wait}s "
                        f"(attempt {attempt + 1}/{self._MAX_RETRIES})"
                    )
                    await asyncio.sleep(wait)
                    continue
                else:
                    raise RuntimeError(
                        f"Racing API error {e.response.status_code}: {e.response.text}"
                    )
            except httpx.RequestError as e:
                raise RuntimeError(f"Network error connecting to Racing API: {e}")

        raise RuntimeError(
            f"Rate limit exceeded after {self._MAX_RETRIES} retries. "
            "Please slow down requests."
        )

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ── Singleton ───────────────────────────────────────────────────────────────────

_racing_client: RacingAPIClient | None = None


def get_racing_client() -> RacingAPIClient:
    global _racing_client
    if _racing_client is None:
        _racing_client = RacingAPIClient()
    return _racing_client
