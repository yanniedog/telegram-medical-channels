# Local runtime data (not in Git)

This directory holds pipeline outputs from discovery, scraping, and normalization.
Paths below are listed in the repo root `.gitignore` and are **not** pushed to GitHub.

| Path | Regenerate |
|------|------------|
| `posts/*.json` | Scrape scripts (`channel_scraper.py`, `concurrent_scrape.py`, etc.) |
| `channels_registry.json`, `rescrape_queue.json` | `python normalize_data.py` |
| `discovered_channels.json`, `agent_discoveries_merged.json` | Discovery / merge scripts |
| `agent_swarm/` shard and swarm JSON | `run_lyzem_shards.py`, swarm writers; see `SWARM_RUNBOOK.md` |
| `agent_swarm_merged.json`, `swarm_tasks.json`, `swarm_checkpoint.json` | `build_swarm_manifest.py`, merge scripts |
| `../channel_seeds.json` | Merged from agent discoveries / seeds pipeline |

Tracked placeholders only: `posts/.gitkeep`, `agent_swarm/.gitkeep`, and this file.
