#!/usr/bin/env python3
"""Full pipeline re-run from scratch."""
from __future__ import annotations
import json, logging, os, subprocess, sys
from pathlib import Path
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("full_rerun")
ROOT = Path(__file__).resolve().parent

def run(cmd, extra=None):
    log.info("RUN %s", " ".join(cmd))
    env = os.environ.copy()
    env["RERUN_FROM_SCRATCH"] = "1"
    env["PYTHONUNBUFFERED"] = "1"
    if extra:
        env.update(extra)
    subprocess.run(cmd, cwd=ROOT, env=env, check=True)

def main():
    py = sys.executable
    scrape_env = {"SCRAPE_WORKERS": os.environ.get("SCRAPE_WORKERS", "40"), "SCRAPE_MAX_PAGES": os.environ.get("SCRAPE_MAX_PAGES", "120")}
    run([py, "normalize_data.py"])
    Path("data/swarm_checkpoint.json").write_text('{"completed":{},"failed":{}}', encoding="utf-8")
    run([py, "build_swarm_manifest.py"])
    run([py, "run_lyzem_shards.py"])
    run([py, "merge_swarm_shards.py"])
    run([py, "parallel_discovery_lyzem.py"])
    run([py, "merge_agent_discoveries.py"])
    run([py, "normalize_data.py"])
    run([py, "concurrent_scrape.py"], scrape_env)
    run([py, "normalize_data.py"])
    run([py, "build_from_cache.py"])
    reg = json.loads(Path("data/channels_registry.json").read_text(encoding="utf-8"))
    q = json.loads(Path("data/rescrape_queue.json").read_text(encoding="utf-8"))
    print(json.dumps({"registry": reg.get("channel_count"), "rescrape_left": len(q)}, indent=2))

if __name__ == "__main__":
    main()
