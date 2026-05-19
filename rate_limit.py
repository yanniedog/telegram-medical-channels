"""Per-host concurrency limits and backoff for HTTP scraping."""
from __future__ import annotations
import asyncio
import os
import random
from typing import Callable, TypeVar
from urllib.parse import urlparse

T = TypeVar("T")
DEFAULT_LIMITS = {
    "t.me": int(os.environ.get("TME_CONCURRENCY", "12")),
    "telegram.me": int(os.environ.get("TME_CONCURRENCY", "12")),
    "lyzem.com": int(os.environ.get("LYZEM_CONCURRENCY", "8")),
    "tgstat.com": int(os.environ.get("TGSTAT_CONCURRENCY", "6")),
}
_host_semaphores: dict[str, asyncio.Semaphore] = {}
_host_lock = asyncio.Lock()

async def semaphore_for_url(url: str) -> asyncio.Semaphore:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if host not in DEFAULT_LIMITS:
        host = "t.me"
    async with _host_lock:
        if host not in _host_semaphores:
            _host_semaphores[host] = asyncio.Semaphore(DEFAULT_LIMITS.get(host, 8))
        return _host_semaphores[host]

def jitter_delay(base: float = 0.05, spread: float = 0.15) -> float:
    return base + random.uniform(0, spread)

async def with_host_limit(url: str, coro_factory: Callable[[], T]) -> T:
    sem = await semaphore_for_url(url)
    async with sem:
        await asyncio.sleep(jitter_delay())
        return await coro_factory()

async def retry_with_backoff(fn: Callable[[], T], url: str = "https://t.me/", max_attempts: int = 4, base_delay: float = 0.5) -> T:
    last_exc = None
    for attempt in range(max_attempts):
        try:
            return await with_host_limit(url, fn)
        except Exception as e:
            last_exc = e
            await asyncio.sleep(base_delay * (2 ** attempt) + random.uniform(0, 0.3))
    if last_exc:
        raise last_exc
    raise RuntimeError("retry_with_backoff failed")
