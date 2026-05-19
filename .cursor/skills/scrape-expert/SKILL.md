---
name: scrape-expert
description: channel_scraper, concurrent_scrape, batch_scrape, telethon_fetch, rate limits.
---

# Scrape expert

Paths: channel_scraper.py, concurrent_scrape.py, batch_scrape.py, tgstat_scraper.py, telethon_fetch.py, rate_limit.py, data/posts/

Env: TME_CONCURRENCY, LYZEM_CONCURRENCY, TGSTAT_CONCURRENCY, SCRAPE_WORKERS

Handoff: data-registry-expert then analytics-workbook-expert. Real fetches only.
