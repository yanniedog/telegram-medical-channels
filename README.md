# Medical Telegram channel analytics

## Output

`medical_telegram_channels_comprehensive.xlsx` — multi-sheet workbook (≤15 tabs) with pivot-ready **Channels_Fact** as the primary table.

## Run

```powershell
cd c:\code\telegram
python normalize_data.py             # clean registry + purge stub caches
python discover_channels.py          # find channels (2k+ subs)
python run_full_analysis.py          # scrape + analyze + build xlsx
# parallel scrape (per-host rate limits):
$env:USE_CONCURRENT_SCRAPE=1; python run_full_analysis.py
python concurrent_scrape.py          # rescrape queue only
# or rebuild xlsx only from cached scrapes:
python build_from_cache.py
```

## Swarm discovery (50+ subagents)

See [SWARM_RUNBOOK.md](SWARM_RUNBOOK.md): `python build_swarm_manifest.py` then wave-spawn Cursor subagents.

## Optional: full history (Telegram API)

Many large channels disable public `t.me/s` previews. For complete PDF/EPUB counts and download stats, set in `.env`:

```
TELEGRAM_API_ID=
TELEGRAM_API_HASH=
```

Then run `python telethon_fetch.py` (requires one-time login).

## Limits

- Public scraping only where Telegram exposes `t.me/s/...` or TGStat lists file posts.
- Download counts are not public; **posts_per_avg_ebook_view** uses view counts as a proxy.
- Publication region/year are inferred from titles, not ISBN metadata.
