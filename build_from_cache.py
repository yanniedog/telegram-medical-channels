#!/usr/bin/env python3
"""Build comprehensive workbook from discovery cache + scraped post JSON."""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from build_workbook import build_comprehensive_workbook
from content_analyzer import (
    analyze_channel,
    channel_requires_direct_files,
    compute_cross_channel_scores,
    is_direct_ebook_post,
    is_ebook_post,
    is_link_only_channel_post,
    normalize_title,
)
from keyword_analyzer import extract_keywords, keywords_long_rows
from health_relevance import include_in_health_workbook, has_books_pdfs_signal, health_relevance_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_cache")

DATA = Path("data")
DISCOVERY = DATA / "discovered_channels.json"
POSTS_DIR = DATA / "posts"
MIN_SUBS = 2000


BLOCKLIST = {
    "nachrichtenportal", "combot", "durov", "tgstat", "lyzem", "telegram",
}


def channel_is_medical(meta: dict) -> bool:
    u = (meta.get("username") or "").lower()
    if u in BLOCKLIST:
        return False
    return include_in_health_workbook(meta, MIN_SUBS)


def infer_source(posts: list[dict]) -> str:
    if not posts:
        return "metadata_only"
    src = posts[0].get("_source", "tme")
    if len(posts) >= 200:
        return "tme_full_preview"
    if src == "tgstat_sample":
        return "tgstat_sample"
    if src == "telemetr_sample":
        return "telemetr_sample"
    if len(posts) >= 30:
        return "tme_partial_preview"
    return src


def main() -> None:
    raw = json.loads(DISCOVERY.read_text(encoding="utf-8"))
    qualified = raw.get("qualified") or {}
    medical = {k: v for k, v in qualified.items() if channel_is_medical(v)}
    log.info("Qualified medical channels: %s", len(medical))

    analyses = []
    all_titles: dict[str, set[str]] = {}
    posts_rows: list[dict] = []
    keywords_rows: list[dict] = []
    excluded: list[dict] = []

    for key, meta in sorted(medical.items(), key=lambda x: -(x[1].get("subscribers") or 0)):
        uname = meta.get("username") or key
        cache = POSTS_DIR / f"{uname.lower()}.json"
        posts = []
        if cache.exists():
            posts = json.loads(cache.read_text(encoding="utf-8"))
        source = infer_source(posts)

        direct_ebook_count = sum(1 for p in posts if is_direct_ebook_post(p))
        if (meta.get("subscribers") or 0) < MIN_SUBS:
            excluded.append({"username": uname, "reason": "below_2000_subscribers", "subscribers": meta.get("subscribers")})
            continue

        if not posts:
            excluded.append(
                {
                    "username": uname,
                    "reason": "no_scrape_cannot_verify_direct_files",
                    "subscribers": meta.get("subscribers"),
                }
            )
            continue

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

        a = analyze_channel(uname, posts, meta.get("subscribers"), source, meta)
        if direct_ebook_count < 3:
            a.notes = (a.notes or "") + f" Only {direct_ebook_count} direct Telegram file(s) in sample."
        if source == "metadata_only":
            a.data_coverage_pct = 0.0
        kw = extract_keywords(posts, meta)
        keywords_rows.extend(keywords_long_rows(uname, kw))
        titles = set()
        for p in posts:
            if is_direct_ebook_post(p):
                nt = normalize_title(p.get("text") or "", p.get("file_names") or [])
                if len(nt) > 8:
                    titles.add(nt)
        all_titles[uname.lower()] = titles
        analyses.append(a)
        for p in posts:
            if is_direct_ebook_post(p):
                posts_rows.append({**p, "channel_username": uname})

    compute_cross_channel_scores(analyses, all_titles)

    out = Path("medical_telegram_channels_comprehensive.xlsx")
    build_comprehensive_workbook(
        out_path=out,
        analyses=analyses,
        posts_rows=posts_rows,
        keywords_rows=keywords_rows,
        excluded=excluded,
        discovery_meta=medical,
        run_meta={
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "min_subscribers": MIN_SUBS,
            "channels_in_fact_table": len(analyses),
            "channels_excluded": len(excluded),
            "method": "t.me/s pagination + TGStat file posts; direct Telegram-hosted ebooks only",
            "direct_hosted_ebooks_only": True,
        },
    )
    log.info("Wrote %s with %s channel rows, %s excluded", out, len(analyses), len(excluded))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log.exception("failed")
        sys.exit(1)
