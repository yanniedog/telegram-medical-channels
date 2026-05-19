#!/usr/bin/env python3
"""Exhaustive Lyzem discovery across all specialty query groups."""
from __future__ import annotations

import json
import time
from pathlib import Path

import httpx

from discover_channels import fetch_channel_meta, scrape_lyzem_page

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MIN_SUBS = 2000
OUT = Path("data/discovered_channels.json")
QUERIES_FILE = Path("specialty_search_queries.json")


def main() -> None:
    groups = json.loads(QUERIES_FILE.read_text(encoding="utf-8"))
    all_queries: list[str] = []
    for qs in groups.values():
        all_queries.extend(qs)
    all_queries = list(dict.fromkeys(all_queries))
    print("queries", len(all_queries))

    seen: set[str] = set()
    if Path("channel_seeds.json").exists():
        seen.update(u.lower() for u in json.loads(Path("channel_seeds.json").read_text(encoding="utf-8")))
    if OUT.exists():
        raw = json.loads(OUT.read_text(encoding="utf-8"))
        seen.update(raw.get("all", {}).keys())

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for q in all_queries:
            for page in range(1, 12):
                for h in scrape_lyzem_page(client, q, page):
                    seen.add(h.lower())
                time.sleep(0.3)
            time.sleep(0.4)
        print("unique handles", len(seen))

        all_meta: dict = {}
        if OUT.exists():
            all_meta = json.loads(OUT.read_text(encoding="utf-8")).get("all", {})

        agent_path = Path("data/agent_discoveries_merged.json")
        agent_tags: dict[str, list] = {}
        if agent_path.exists():
            for e in json.loads(agent_path.read_text(encoding="utf-8")):
                agent_tags[e["username"].lower()] = e.get("specialty_tags", [])

        for i, uname in enumerate(sorted(seen)):
            if uname in all_meta and (all_meta[uname].get("subscribers") or 0) >= MIN_SUBS:
                continue
            meta = fetch_channel_meta(client, uname)
            if meta.get("error"):
                continue
            if uname in agent_tags:
                meta["agent_specialty_tags"] = agent_tags[uname]
            all_meta[uname] = meta
            if (i + 1) % 25 == 0:
                qn = sum(1 for v in all_meta.values() if (v.get("subscribers") or 0) >= MIN_SUBS)
                print(f"{i+1}/{len(seen)} qualified={qn}")
            time.sleep(0.25)

    qualified = {k: v for k, v in all_meta.items() if (v.get("subscribers") or 0) >= MIN_SUBS}
    OUT.write_text(
        json.dumps({"qualified": qualified, "all": all_meta}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    seeds = sorted(qualified.keys())
    Path("channel_seeds.json").write_text(json.dumps(seeds, indent=2), encoding="utf-8")
    print("qualified", len(qualified), "all", len(all_meta))


if __name__ == "__main__":
    main()
