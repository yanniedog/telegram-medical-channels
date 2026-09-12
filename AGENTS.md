# telegram-medical-channels — Agent configuration

Medical Telegram channel discovery, scraping, registry normalization, and workbook analytics. **Windows local PC only** — no Pi, no SSH, no Cloudflare.

Workflow mirrors **AR-local** / **Australian Rates** for Git, PR, CI, and bot/thread closure. **Verification is local Python pipeline** (`npm run verify:local`), not a dashboard or production URL.

## Ship bar

Full procedure — branch, commit, PR, CI, bot wait, feedback synthesis, thread closure, merge, **local verify** — all steps required unless the user explicitly waives in writing for that PR.

**Read `WORKFLOW.md` in full** before opening or merging a PR.

Anti-early-stop:

```powershell
npm run ship:closeout:strict ; npm run wait-for-bots
```

- Exit **2** from `ship:closeout:strict` → open PR still exists; continue `WORKFLOW.md` steps 5–9.
- Exit **2** from `wait-for-bots` → wait for the minimum bot window, then re-sweep.

Cursor rules live under **`.cursor/rules/`**.

## Multiagent workflow and modular code

- Fresh **`origin/main`**, distinctive **`agent/<slug>`** (or feat/fix), no branch reuse across concurrent agents.
- Rebase/merge when stale; resolve overlaps with other topic branches deliberately.
- **Green CI ≠ merge-ready** — complete wait gate, synthesis, and threaded replies per **`WORKFLOW.md`**.
- **Soft target ~800 LOC per file**, **hard ceiling ~1000 LOC**; split along natural seams when adding non-trivial code.
- **~50 lines per function** where practical; avoid copying the same logic in 3+ places.

Exemptions: lockfiles, `.env*`, all paths in **`.gitignore`** under `data/` and generated workbooks (rebuild registry with `normalize_data.py`, workbook with `build_from_cache.py`). `channel_seeds.json` is gitignored and rebuilt by discovery/merge scripts.

## Local verification (replaces dashboard)

| Step | Command |
|------|---------|
| Registry normalize | `python normalize_data.py` |
| Workbook from cache | `python build_from_cache.py` |
| Full pipeline smoke (optional, long) | `python run_full_rerun.py` |
| Ship-bar verify script | `npm run verify:local` |
| Full network rerun verify | `npm run verify:local -- --full-rerun` |

Requires **Python**, **Node** (for `wait-for-bots`), and **`gh`** CLI for PR steps.

## Repo commands

| Purpose | Command |
|--------|---------|
| Bot wait gate (new PR) | `npm run wait-for-bots` |
| Closeout: open PR check | `npm run ship:closeout:strict` |
| Local pipeline smoke | `npm run verify:local` |
| Prune remote refs | `npm run git:graph-hygiene` |

## Project philosophy: real data only

**No mock or fabricated Telegram posts** for acceptance. Discovery uses **Lyzem**, **t.me**, **TGStat** (and Telethon when configured). Scraped content lives under **`data/posts/`** from real fetches.

See **`SWARM_RUNBOOK.md`** for 50+ subagent discovery waves.

## Key scripts (reference)

| Area | Scripts |
|------|---------|
| Discovery | `build_swarm_manifest.py`, `run_lyzem_shards.py`, `merge_swarm_shards.py`, `merge_agent_discoveries.py`, `channel_seeds.json` |
| Scrape | `channel_scraper.py`, `concurrent_scrape.py`, `batch_scrape.py`, `tgstat_scraper.py`, `telethon_fetch.py` |
| Registry | `normalize_data.py`, `channel_registry.py`, `data/channels_registry.json`, `data/rescrape_queue.json` |
| Relevance | `health_relevance.py`, `content_analyzer.py` |
| Workbook | `build_workbook.py`, `build_from_cache.py`, `keyword_analyzer.py` |
| Pipeline | `run_full_rerun.py`, `rate_limit.py` |


## Autonomous operations

You do **not** need to say **"run chief agent"** each session. **Hooks + always-on rules** enforce chief-first coordination:

| Trigger | What happens |
|---------|----------------|
| sessionStart | Hook reminds parent to spawn chief (run_in_background=true) |
| subagentStop / stop | Hook reminds after substantive work (5 min dedupe) |
| Dirty tree / open PRs | Stronger reminder: chief before feature edits; partition into agent/<slug> PRs |

**Not a 24/7 daemon** — automation is maximized **inside Cursor** only. Enable **Cursor Hooks** in settings if disabled.

## Multi-agent team (10 roles)

See **TEAM.md** for roster, delegation flow, and invoke phrases.

| Role | Skill / rule |
|------|----------------|
| Chief (spawn first) | [`.cursor/skills/chief-agent/SKILL.md`](.cursor/skills/chief-agent/SKILL.md), [`.cursor/rules/chief-agent-always.mdc`](.cursor/rules/chief-agent-always.mdc) |
| Workflow orchestrator | [`.cursor/skills/workflow-orchestrator/SKILL.md`](.cursor/skills/workflow-orchestrator/SKILL.md), [`.cursor/rules/workflow-orchestrator-always.mdc`](.cursor/rules/workflow-orchestrator-always.mdc) |
| PR fix / babysit | [`.cursor/skills/pr-fix-agent/SKILL.md`](.cursor/skills/pr-fix-agent/SKILL.md) |
| Explore (readonly) | [`.cursor/skills/explore-agent/SKILL.md`](.cursor/skills/explore-agent/SKILL.md) |
| Domain experts (6) | `.cursor/skills/*-expert/SKILL.md` — routed by orchestrator |

**Manual chief / orchestrator** (optional): say **"run chief agent"** or **"run workflow orchestrator"** — hooks handle normal sessions.

Hook reminder: [`.cursor/hooks/orchestrator-remind.mjs`](.cursor/hooks/orchestrator-remind.mjs).

## Debugging

- Use **fresh scrape/registry state** and script stdout/stderr, not stale assumptions.
- If **`frequent_errors.txt`** exists in the repo root, check fixes against known recurring failures before claiming scripts are fine.
