#!/usr/bin/env python3
"""Parallel channel scrape with per-host rate limits."""
from __future__ import annotations
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from merge_agent_discoveries import DATA, load_registry, normalize_username, save_registry
from rate_limit import retry_with_backoff

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("concurrent_scrape")
DISCOVERY_PATH = DATA / "discovered_channels.json"
RESCRAPE_QUEUE_PATH = DATA / "rescrape_queue.json"

def load_scrape_targets():
    targets = {}
    disc_meta: dict = {}
    if DISCOVERY_PATH.exists():
        raw = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
        disc_meta = raw.get("qualified") or raw.get("all") or {}
    if RESCRAPE_QUEUE_PATH.exists():
        for u in json.loads(RESCRAPE_QUEUE_PATH.read_text(encoding="utf-8")):
            un = normalize_username(u)
            meta = disc_meta.get(un) or {}
            targets[un] = {
                "username": un,
                "subscribers": meta.get("subscribers"),
                "title": meta.get("title"),
            }
    if (DATA / "channels_registry.json").exists():
        for u, rec in load_registry().items():
            if rec.get("post_cache_quality") in ("missing", "stub", "partial"):
                if u not in targets:
                    targets[u] = {"username": u, "subscribers": rec.get("subscribers"), "title": rec.get("title")}
    items = sorted(targets.items(), key=lambda x: -(x[1].get("subscribers") or 0))
    cap = int(os.environ.get("MAX_SCRAPE_CHANNELS", "0"))
    if cap > 0:
        items = items[:cap]
    return items

async def scrape_one_async(username, meta):
    from run_full_analysis import scrape_one
    uname = meta.get("username") or username
    loop = asyncio.get_event_loop()

    async def _run():
        return await loop.run_in_executor(None, scrape_one, uname, meta)

    posts, source = await retry_with_backoff(_run, url=f"https://t.me/{uname}")
    return uname, len(posts), source

async def scrape_medical_channels(medical, workers):
    sem = asyncio.Semaphore(workers)
    async def worker(username, meta):
        async with sem:
            r = await scrape_one_async(username, meta)
            log.info("OK @%s posts=%s source=%s", r[0], r[1], r[2])
    await asyncio.gather(*[worker(u, m) for u, m in medical.items()])

async def run_pool(workers):
    items = load_scrape_targets()
    if not items:
        log.info("No scrape targets")
        return
    attempted = {u for u, _ in items}
    prior: set[str] = set()
    if RESCRAPE_QUEUE_PATH.exists():
        prior = set(json.loads(RESCRAPE_QUEUE_PATH.read_text(encoding="utf-8")))
    sem = asyncio.Semaphore(workers)
    errors = []
    async def worker(username, meta):
        async with sem:
            try:
                r = await scrape_one_async(username, meta)
                if r[1]:
                    log.info("OK @%s posts=%s source=%s", r[0], r[1], r[2])
                else:
                    log.warning("EMPTY @%s (no scrapable posts)", r[0])
            except Exception as e:
                errors.append(f"{username}: {e}")
                log.error("FAIL @%s: %s", username, e)
    await asyncio.gather(*[worker(u, m) for u, m in items])
    still_missing = {u for u in attempted if not (DATA / "posts" / f"{u}.json").exists()}
    remaining = sorted((prior - attempted) | still_missing)
    RESCRAPE_QUEUE_PATH.write_text(json.dumps(remaining, indent=2), encoding="utf-8")
    if (DATA / "channels_registry.json").exists():
        save_registry(load_registry())
    log.info("Done errors=%s remaining=%s", len(errors), len(remaining))

def main():
    workers = int(os.environ.get("SCRAPE_WORKERS", "40"))
    asyncio.run(run_pool(workers))

if __name__ == "__main__":
    main()
