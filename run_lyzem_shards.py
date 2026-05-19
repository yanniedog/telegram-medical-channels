#!/usr/bin/env python3
"""Execute swarm_tasks.json Lyzem shards."""
from __future__ import annotations
import asyncio, json, logging, os, re, sys, time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from discover_channels import fetch_channel_meta, scrape_lyzem_page
from health_relevance import include_in_health_workbook

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lyzem_shards")
DATA = Path("data")
MANIFEST = DATA / "swarm_tasks.json"
CHECKPOINT = DATA / "swarm_checkpoint.json"
MIN_SUBS = 2000
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
WORKERS = int(os.environ.get("LYZEM_SHARD_WORKERS", "12"))
_cp = {}

def shard_done(path, cp):
    return path.name in cp.get("completed", {}) or (path.exists() and path.stat().st_size > 10)

def run_shard_sync(shard, client):
    out, seen = [], set()
    spec = shard.get("specialty", "")
    src = shard.get("discovery_source", "lyzem_shard")
    for query in shard.get("queries") or []:
        for page in shard.get("pages") or [1,2,3]:
            for h in scrape_lyzem_page(client, query, page):
                seen.add(h.lower())
            time.sleep(0.25)
        time.sleep(0.3)
    for uname in sorted(seen):
        meta = fetch_channel_meta(client, uname)
        if meta.get("error"):
            continue
        subs = meta.get("subscribers") or 0
        if subs < MIN_SUBS or not include_in_health_workbook(meta, MIN_SUBS):
            continue
        title = (meta.get("title") or "") + " " + (meta.get("description") or "")
        out.append({"username": uname, "subscribers_estimate": subs, "specialty_tags": [spec] if spec else [],
            "has_direct_ebooks": bool(re.search(r"book|pdf|ebook|library|medical", title, re.I)),
            "source_url": meta.get("link") or f"https://t.me/{uname}", "discovery_source": src, "title": meta.get("title")})
        time.sleep(0.22)
    return out

async def run_shard(shard, sem):
    path = Path(shard["output"])
    async with sem:
        if shard_done(path, _cp):
            return path.name, True, "skip"
        def work():
            with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=35) as c:
                return run_shard_sync(shard, c)
        loop = asyncio.get_event_loop()
        try:
            rows = await loop.run_in_executor(None, work)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
            return path.name, True, str(len(rows))
        except Exception as e:
            return path.name, False, str(e)

async def main_async():
    global _cp
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    shards = [s for s in manifest["shards"] if s.get("queries")]
    _cp = json.loads(CHECKPOINT.read_text(encoding="utf-8")) if CHECKPOINT.exists() else {"completed": {}, "failed": {}}
    log.info("shards=%s workers=%s", len(shards), WORKERS)
    sem = asyncio.Semaphore(WORKERS)
    res = await asyncio.gather(*[run_shard(s, sem) for s in shards])
    now = datetime.now(timezone.utc).isoformat()
    ok = fail = skip = 0
    for name, success, msg in res:
        if msg == "skip":
            skip += 1
        elif success:
            _cp.setdefault("completed", {})[name] = now
            ok += 1
            log.info("%s -> %s", name, msg)
        else:
            _cp.setdefault("failed", {})[name] = msg
            fail += 1
    _cp["last_run_at"] = now
    CHECKPOINT.write_text(json.dumps(_cp, indent=2), encoding="utf-8")
    log.info("done ok=%s skip=%s fail=%s", ok, skip, fail)

if __name__ == "__main__":
    asyncio.run(main_async())
