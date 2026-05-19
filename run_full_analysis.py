#!/usr/bin/env python3
"""
Full pipeline: discover -> scrape -> analyze -> Excel workbook.
Uses public t.me/s previews + TGStat samples. Optional Telethon via .env.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from build_workbook import build_comprehensive_workbook
from channel_scraper import scrape_channel, save_posts
from content_analyzer import (
    analyze_channel,
    channel_requires_direct_files,
    compute_cross_channel_scores,
    is_direct_ebook_post,
    is_ebook_post,
    is_link_only_channel_post,
    normalize_title,
)
from discover_channels import SEED_USERNAMES, fetch_channel_meta, scrape_lyzem_page, parse_subscribers
from tgstat_scraper import scrape_tgstat_channel

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("analysis.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("pipeline")

DATA = Path("data")
POSTS_DIR = DATA / "posts"
DISCOVERY_PATH = DATA / "discovered_channels.json"
MIN_SUBS = 2000
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def load_or_discover() -> dict[str, dict]:
    seeds_path = Path("channel_seeds.json")
    seed_list = json.loads(seeds_path.read_text(encoding="utf-8")) if seeds_path.exists() else SEED_USERNAMES
    seen = {u.lower() for u in seed_list}
    seen.update(u.lower() for u in SEED_USERNAMES)

    if DISCOVERY_PATH.exists() and not os.environ.get("FORCE_REDISCOVER"):
        raw = json.loads(DISCOVERY_PATH.read_text(encoding="utf-8"))
        qualified = raw.get("qualified") or {}
        if len(qualified) >= 10:
            log.info("Loaded discovery cache: %s channels", len(qualified))
            return qualified

    log.info("Running discovery on %s seed handles + lyzem...", len(seen))
    from discover_channels import QUERIES

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for q in QUERIES[:8]:
            for page in range(1, 3):
                for h in scrape_lyzem_page(client, q, page):
                    seen.add(h.lower())
                time.sleep(0.4)

        all_meta: dict[str, dict] = {}
        for uname in sorted(seen):
            try:
                meta = fetch_channel_meta(client, uname)
            except Exception as e:
                log.warning("meta fail %s: %s", uname, e)
                continue
            if meta.get("error"):
                continue
            all_meta[uname.lower()] = meta
            time.sleep(0.32)

    qualified = {k: v for k, v in all_meta.items() if (v.get("subscribers") or 0) >= MIN_SUBS}
    DATA.mkdir(exist_ok=True)
    DISCOVERY_PATH.write_text(
        json.dumps(
            {"qualified": qualified, "all": all_meta, "discovered_at": datetime.now(timezone.utc).isoformat()},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("Discovery done: qualified=%s all=%s", len(qualified), len(all_meta))
    return qualified


def channel_is_medical(meta: dict) -> bool:
    from health_relevance import include_in_health_workbook
    return include_in_health_workbook(meta, MIN_SUBS)


def scrape_one(username: str, meta: dict) -> tuple[list[dict], str]:
    uname = (meta.get("username") or username).lstrip("@")
    cache = POSTS_DIR / f"{uname.lower()}.json"
    if cache.exists():
        posts = json.loads(cache.read_text(encoding="utf-8"))
        from content_analyzer import is_ebook_post, is_link_only_channel_post

        direct = sum(1 for p in posts if is_direct_ebook_post(p))
        # Re-scrape stale/bad TGStat bot-placeholder caches
        if direct >= 3 and len(posts) >= 30:
            return posts, "cache"
        if direct >= 1 and len(posts) >= 100:
            return posts, "cache"
        log.info("Refreshing cache for @%s (posts=%s direct_ebooks=%s)", uname, len(posts), direct)
        cache.unlink(missing_ok=True)

    from dataclasses import asdict

    scraped = []
    candidates = list(dict.fromkeys([uname, uname.lower(), username, username.lower()]))
    for cand in candidates:
        log.info("Trying t.me/s/%s ...", cand)
        max_p = int(os.environ.get("SCRAPE_MAX_PAGES", "120"))
        scraped = scrape_channel(cand, max_pages=max_p, delay=0.35)
        if len(scraped) >= 30:
            posts = [asdict(s) for s in scraped]
            POSTS_DIR.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
            return posts, "tme_full_preview"
    if scraped:
        posts = [asdict(s) for s in scraped]
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        return posts, "tme_partial_preview"

    log.info("TGStat sample for %s (no public preview)", uname)
    posts = scrape_tgstat_channel(uname)
    if not posts and uname.lower() != uname:
        posts = scrape_tgstat_channel(uname.lower())
    if posts:
        POSTS_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        return posts, "tgstat_sample"
    return [], "no_public_data"


def main() -> None:
    DATA.mkdir(exist_ok=True)
    POSTS_DIR.mkdir(exist_ok=True)

    qualified = load_or_discover()
    medical = {k: v for k, v in qualified.items() if channel_is_medical(v)}
    log.info("Medical channels with >=%s subs: %s", MIN_SUBS, len(medical))

    if os.environ.get("USE_CONCURRENT_SCRAPE"):
        import asyncio

        from concurrent_scrape import scrape_medical_channels

        workers = int(os.environ.get("SCRAPE_WORKERS", "40"))
        log.info("Concurrent scrape enabled (workers=%s)", workers)
        asyncio.run(scrape_medical_channels(medical, workers))

    analyses = []
    all_titles: dict[str, set[str]] = {}
    posts_rows = []
    excluded = []

    for username, meta in sorted(medical.items(), key=lambda x: -(x[1].get("subscribers") or 0)):
        uname = meta.get("username") or username
        posts, source = scrape_one(uname, meta)
        if not posts:
            excluded.append({"username": uname, "reason": "no_scrapable_posts", "subscribers": meta.get("subscribers")})
            continue

        direct_ebook_count = sum(1 for p in posts if is_direct_ebook_post(p))
        ok_direct, direct_reason = channel_requires_direct_files(posts, min_direct=1)
        if not ok_direct:
            excluded.append(
                {
                    "username": uname,
                    "reason": direct_reason,
                    "subscribers": meta.get("subscribers"),
                    "posts_sampled": len(posts),
                    "direct_ebooks_in_sample": direct_ebook_count,
                    "source": source,
                }
            )
            continue

        analysis = analyze_channel(uname, posts, meta.get("subscribers"), source)
        titles = set()
        for p in posts:
            if is_direct_ebook_post(p):
                nt = normalize_title(p.get("text") or "", p.get("file_names") or [])
                if len(nt) > 8:
                    titles.add(nt)
        all_titles[uname.lower()] = titles
        analyses.append(analysis)

        for p in posts:
            if not is_direct_ebook_post(p):
                continue
            posts_rows.append({**p, "channel_username": uname})

        log.info(
            "OK @%s direct_ebooks=%s posts=%s source=%s",
            uname,
            analysis.ebook_posts,
            analysis.posts_scraped,
            source,
        )

    compute_cross_channel_scores(analyses, all_titles)

    out_xlsx = Path("medical_telegram_channels_comprehensive.xlsx")
    from keyword_analyzer import extract_keywords, keywords_long_rows

    keywords_rows: list[dict] = []
    for a in analyses:
        cache = POSTS_DIR / f"{a.username.lower()}.json"
        posts = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else []
        kw = extract_keywords(posts, medical.get(a.username.lower(), {}))
        keywords_rows.extend(keywords_long_rows(a.username, kw))

    build_comprehensive_workbook(
        out_path=out_xlsx,
        analyses=analyses,
        posts_rows=posts_rows,
        keywords_rows=keywords_rows,
        excluded=excluded,
        discovery_meta=medical,
        run_meta={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "min_subscribers": MIN_SUBS,
            "channels_analyzed": len(analyses),
            "method": "Public t.me/s pagination + TGStat samples; no Telegram API session",
        },
    )
    log.info("Wrote %s (%s channels)", out_xlsx, len(analyses))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("Pipeline failed")
        sys.exit(1)
