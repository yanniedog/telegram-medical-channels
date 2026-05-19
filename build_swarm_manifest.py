#!/usr/bin/env python3
"""Build swarm_tasks.json with 72+ Lyzem discovery shards."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

DATA = Path("data")
SWARM_DIR = DATA / "agent_swarm"
MANIFEST_PATH = DATA / "swarm_tasks.json"
CHECKPOINT_PATH = DATA / "swarm_checkpoint.json"
QUERIES_PATH = Path("specialty_search_queries.json")
REGISTRY_PATH = DATA / "channels_registry.json"
PAGES = [1, 2, 3]

def load_missing_meta_channels():
    if not REGISTRY_PATH.exists():
        return []
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    channels = raw.get("channels") or raw
    return sorted([u for u, rec in channels.items() if rec.get("post_cache_quality") in ("missing", "stub")])[:40]

def build_shards():
    queries_map = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    shards = []
    shard_id = 0
    for specialty, queries in queries_map.items():
        for query in queries:
            shard_id += 1
            out = SWARM_DIR / f"shard_{shard_id:03d}.json"
            shards.append({"shard_id": shard_id, "specialty": specialty, "queries": [query], "pages": PAGES,
                "output": str(out).replace("\\", "/"), "discovery_source": f"lyzem_shard_{shard_id:03d}",
                "prompt": f'Search Lyzem for: "{query}" pages 1-3. Write JSON array to {out}.'})
    for username in load_missing_meta_channels():
        shard_id += 1
        out = SWARM_DIR / f"meta_{shard_id:03d}.json"
        shards.append({"shard_id": shard_id, "specialty": "meta_fetch", "queries": [], "pages": [], "username": username,
            "output": str(out).replace("\\", "/"), "discovery_source": f"meta_shard_{shard_id:03d}",
            "prompt": f"Fetch t.me metadata for @{username} if medical books channel >=2000 subs."})
    return shards

def main():
    SWARM_DIR.mkdir(parents=True, exist_ok=True)
    shards = build_shards()
    if len(shards) < 50:
        sys.exit(f"only {len(shards)} shards")
    manifest = {"generated_at": datetime.now(timezone.utc).isoformat(), "shard_count": len(shards),
        "wave_size": 15, "wave_gap_seconds": 2.5, "shards": shards}
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    cp = {"created_at": datetime.now(timezone.utc).isoformat(), "completed": {}, "failed": {}, "total_shards": len(shards)}
    if CHECKPOINT_PATH.exists():
        cp = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
        cp["total_shards"] = len(shards)
    CHECKPOINT_PATH.write_text(json.dumps(cp, indent=2), encoding="utf-8")
    print(f"Wrote {len(shards)} shards -> {MANIFEST_PATH}")

if __name__ == "__main__":
    main()
