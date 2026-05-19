#!/usr/bin/env python3
"""Batch-scrape all qualified channels (respectful rate limits)."""
from __future__ import annotations

import json
import logging
import sys
import time
from dataclasses import asdict
from pathlib import Path

from channel_scraper import scrape_channel
from run_full_analysis import scrape_one
from tgstat_scraper import scrape_tgstat_channel

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("batch_scrape")

DATA = Path("data")
DISCOVERY = DATA / "discovered_channels.json"
POSTS_DIR = DATA / "posts"
MAX_PAGES = 120


def main() -> None:
    raw = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    qualified = raw.get("qualified") or {}
    keys = sorted(qualified.keys(), key=lambda k: -(qualified[k].get("subscribers") or 0))
    log.info("Scraping %s qualified channels (max_pages=%s)", len(keys), MAX_PAGES)

    for i, key in enumerate(keys):
        meta = qualified[key]
        uname = meta.get("username") or key
        cache = POSTS_DIR / f"{uname.lower()}.json"
        if cache.exists() and cache.stat().st_size > 8000:
            log.info("[%s/%s] skip @%s (cached)", i + 1, len(keys), uname)
            continue
        try:
            posts, source = scrape_one(uname, meta)
            log.info("[%s/%s] @%s posts=%s source=%s", i + 1, len(keys), uname, len(posts), source)
        except Exception as e:
            log.error("[%s/%s] @%s FAILED: %s", i + 1, len(keys), uname, e)
            sys.exit(1)
        time.sleep(0.5)

    log.info("Batch scrape complete")


if __name__ == "__main__":
    main()
