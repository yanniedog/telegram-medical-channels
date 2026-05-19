#!/usr/bin/env python3
"""Merge agent_swarm shard JSON into registry and discovery caches."""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from merge_agent_discoveries import ingest_discovery_file, load_registry, save_registry, sync_channel_seeds, sync_discovered_channels

DATA = Path("data")
SWARM_DIR = DATA / "agent_swarm"
CHECKPOINT_PATH = DATA / "swarm_checkpoint.json"
MERGED_SWARM_PATH = DATA / "agent_swarm_merged.json"

def shard_paths():
    paths = []
    if SWARM_DIR.is_dir():
        paths.extend(sorted(SWARM_DIR.glob("shard_*.json")))
        paths.extend(sorted(SWARM_DIR.glob("meta_*.json")))
    return paths

def merge_shard_files():
    by_user = {}
    for path in shard_paths():
        if not path.exists() or path.stat().st_size < 3:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not isinstance(raw, list):
            continue
        for item in raw:
            u = (item.get("username") or "").lstrip("@").lower()
            if u:
                by_user[u] = item
    return by_user

def update_checkpoint(completed):
    cp = {}
    if CHECKPOINT_PATH.exists():
        cp = json.loads(CHECKPOINT_PATH.read_text(encoding="utf-8"))
    comp = cp.setdefault("completed", {})
    now = datetime.now(timezone.utc).isoformat()
    for s in completed:
        comp[s] = now
    cp["last_merge_at"] = now
    CHECKPOINT_PATH.write_text(json.dumps(cp, indent=2), encoding="utf-8")

def main():
    reg = load_registry()
    completed = []
    for path in shard_paths():
        ingest_discovery_file(reg, path)
        if path.stat().st_size > 10:
            completed.append(path.name)
    merged = merge_shard_files()
    MERGED_SWARM_PATH.write_text(json.dumps(list(merged.values()), indent=2), encoding="utf-8")
    save_registry(reg)
    sync_discovered_channels(reg)
    sync_channel_seeds(reg)
    update_checkpoint(completed)
    print(f"Merged {len(merged)} shard channels; registry={len(reg)}")

if __name__ == "__main__":
    main()
