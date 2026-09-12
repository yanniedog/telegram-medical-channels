#!/usr/bin/env python3
"""Merge subagent discovery JSON files into master seed + discovery cache."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

DATA = Path("data")
REGISTRY_PATH = DATA / "channels_registry.json"
POSTS_DIR = DATA / "posts"
DISCOVERY_PATH = DATA / "discovered_channels.json"
RESCRAPE_QUEUE_PATH = DATA / "rescrape_queue.json"
MIN_SUBS = 2000

USERNAME_ALIASES: dict[str, str] = {
    "medicalbooksstoress": "medical_books_storess",
    "mccqe": "mccqe_1",
    "million_medical_books": "mmedicalbookss",
}
OFF_TOPIC_USERNAMES = frozenset({"english_for_business"})
BLOCKLIST = frozenset({"nachrichtenportal", "combot", "durov", "tgstat", "lyzem", "telegram"})
TGSTAT_SOURCES = frozenset({"tgstat_sample", "tgstat_text_sample", "telemetr_sample"})


def normalize_username(raw: str | None) -> str:
    u = (raw or "").strip().lstrip("@").lower()
    return USERNAME_ALIASES.get(u, u) if u else ""


def resolve_post_path(username: str) -> Path:
    return POSTS_DIR / f"{normalize_username(username)}.json"


def dedupe_file_extensions(posts: list[dict]) -> int:
    changed = 0
    for p in posts:
        exts = p.get("file_extensions") or []
        if isinstance(exts, list):
            deduped = list(dict.fromkeys(exts))
            if deduped != exts:
                p["file_extensions"] = deduped
                changed += 1
    return changed


def empty_registry_record(username: str) -> dict[str, Any]:
    return {
        "username": username,
        "subscribers": None,
        "title": None,
        "specialty_tags": [],
        "discovery_sources": [],
        "has_post_cache": False,
        "post_cache_quality": "missing",
        "aliases": [],
    }


def classify_post_cache(posts: list[dict] | None) -> str:
    if not posts:
        return "missing"
    if posts[0].get("_source") in TGSTAT_SOURCES:
        return "stub"
    null_dt = sum(1 for p in posts if not p.get("datetime_utc"))
    if len(posts) < 30 and null_dt > len(posts) // 2:
        return "stub"
    if len(posts) >= 200:
        return "full"
    if len(posts) >= 30:
        return "partial"
    return "stub"


def merge_into_registry(reg: dict[str, dict], username: str, patch: dict[str, Any]) -> None:
    u = normalize_username(username)
    if not u or u in BLOCKLIST or u in OFF_TOPIC_USERNAMES:
        return
    if u not in reg:
        reg[u] = {
            "username": u,
            "subscribers": None,
            "title": None,
            "specialty_tags": [],
            "discovery_sources": [],
            "has_post_cache": False,
            "post_cache_quality": "missing",
            "aliases": [],
        }
    rec = reg[u]
    if patch.get("title"):
        rec["title"] = patch["title"]
    subs = patch.get("subscribers") or patch.get("subscribers_estimate")
    if subs is not None:
        try:
            subs = int(subs)
        except (TypeError, ValueError):
            subs = None
        if subs and (rec.get("subscribers") or 0) < subs:
            rec["subscribers"] = subs
    tags = patch.get("specialty_tags") or patch.get("agent_specialty_tags") or []
    if isinstance(tags, str):
        tags = [tags]
    rec["specialty_tags"] = sorted(set(rec.get("specialty_tags", [])) | set(tags))
    ds = patch.get("discovery_source")
    if ds and ds not in rec["discovery_sources"]:
        rec["discovery_sources"].append(ds)


def load_registry() -> dict[str, dict]:
    if not REGISTRY_PATH.exists():
        return {}
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, dict) and "channels" in raw:
        return {normalize_username(k): v for k, v in raw["channels"].items()}
    return {}


def save_registry(reg: dict[str, dict]) -> None:
    DATA.mkdir(exist_ok=True)
    for rec in reg.values():
        pp = resolve_post_path(rec["username"])
        rec["has_post_cache"] = pp.exists()
        if rec["has_post_cache"]:
            try:
                rec["post_cache_quality"] = classify_post_cache(json.loads(pp.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                rec["post_cache_quality"] = "missing"
                rec["has_post_cache"] = False
        else:
            rec["post_cache_quality"] = "missing"
    REGISTRY_PATH.write_text(
        json.dumps({"version": 1, "channel_count": len(reg), "channels": dict(sorted(reg.items()))}, indent=2),
        encoding="utf-8",
    )


def normalize_discovery_entry(e: dict) -> dict:
    tags = e.get("specialty_tags") or []
    if isinstance(tags, str):
        tags = [tags]
    return {
        "username": normalize_username(e.get("username")),
        "subscribers": e.get("subscribers") or e.get("subscribers_estimate"),
        "title": e.get("title"),
        "specialty_tags": tags,
        "discovery_source": e.get("discovery_source") or "unknown",
        "source_url": e.get("source_url"),
        "has_direct_ebooks": e.get("has_direct_ebooks"),
    }


def ingest_discovery_file(reg: dict[str, dict], path: Path) -> int:
    if path.name == "test.json":
        return 0
    n = 0
    if not path.exists():
        return 0
    try:
        raw = json.loads(path.read_bytes())
    except json.JSONDecodeError:
        return 0
    if not isinstance(raw, list):
        return 0
    for item in raw:
        e = normalize_discovery_entry(item)
        if not e["username"]:
            continue
        merge_into_registry(
            reg,
            e["username"],
            {
                "subscribers": e.get("subscribers"),
                "title": e.get("title"),
                "specialty_tags": e.get("specialty_tags"),
                "discovery_source": e.get("discovery_source") or path.stem,
            },
        )
        n += 1
    return n


def sync_discovered_channels(reg: dict[str, dict]) -> None:
    all_meta = {
        u: {
            "username": u,
            "title": rec.get("title"),
            "subscribers": rec.get("subscribers"),
            "agent_specialty_tags": rec.get("specialty_tags", []),
            "link": f"https://t.me/{u}",
        }
        for u, rec in reg.items()
    }
    qualified = {k: v for k, v in all_meta.items() if (v.get("subscribers") or 0) >= MIN_SUBS}
    DISCOVERY_PATH.write_text(json.dumps({"qualified": qualified, "all": all_meta}, indent=2), encoding="utf-8")


def sync_channel_seeds(reg: dict[str, dict]) -> None:
    seeds = sorted(u for u in reg if u not in OFF_TOPIC_USERNAMES and u not in BLOCKLIST)
    Path("channel_seeds.json").write_text(json.dumps(seeds, indent=2), encoding="utf-8")


AGENT_FILES = [
    DATA / "agent_au.json",
    DATA / "agent_surgery.json",
    DATA / "agent_radiology_pathology.json",
    DATA / "agent_psych_gp_em.json",
    DATA / "agent_dental_pharm_eye.json",
    DATA / "agent_internal_medicine.json",
    DATA / "agent_mbbs_general.json",
    DATA / "agent_obgyn_paeds_anaes.json",
    DATA / "agent_dermatology_nursing.json",
]


def normalize_entry(e: dict) -> dict:
    return normalize_discovery_entry(e)


def swarm_json_paths() -> list[Path]:
    paths: list[Path] = []
    swarm = DATA / "agent_swarm"
    if swarm.is_dir():
        for p in sorted(swarm.glob("*.json")):
            if p.name == "test.json":
                continue
            paths.append(p)
    return paths


def merge_all(extra_paths: list[Path] | None = None) -> dict[str, dict]:
    by_user: dict[str, dict] = {}
    paths = [p for p in AGENT_FILES if p.exists()]
    paths.extend(swarm_json_paths())
    paths.extend(extra_paths or [])
    merged_path = DATA / "agent_discoveries_merged.json"
    if merged_path.exists() and merged_path not in paths:
        paths.append(merged_path)

    seen_paths: set[str] = set()
    for p in paths:
        key = str(p.resolve())
        if key in seen_paths:
            continue
        seen_paths.add(key)
        items = []
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if isinstance(raw, list):
                items = raw
        for raw in items:
            e = normalize_entry(raw)
            u = e["username"]
            if not u or len(u) < 3:
                continue
            if u in by_user:
                by_user[u]["specialty_tags"] = sorted(
                    set(by_user[u].get("specialty_tags", []) + e["specialty_tags"])
                )
                sub = e.get("subscribers") or 0
                if sub > (by_user[u].get("subscribers_estimate") or 0):
                    by_user[u]["subscribers_estimate"] = sub
            else:
                by_user[u] = {
                    "username": u,
                    "subscribers_estimate": e.get("subscribers"),
                    "specialty_tags": e.get("specialty_tags", []),
                    "has_direct_ebooks": e.get("has_direct_ebooks"),
                    "source_url": e.get("source_url"),
                    "discovery_source": e.get("discovery_source", "subagent"),
                }
    return by_user


def main() -> None:
    merged = merge_all()
    out = DATA / "agent_discoveries_merged.json"
    out.write_text(
        json.dumps(list(merged.values()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reg = load_registry() if (DATA / "channels_registry.json").exists() else {}
    for u, e in merged.items():
        merge_into_registry(
            reg,
            u,
            {
                "subscribers": e.get("subscribers_estimate"),
                "specialty_tags": e.get("specialty_tags", []),
                "discovery_source": e.get("discovery_source", "subagent"),
            },
        )
    for p in swarm_json_paths():
        ingest_discovery_file(reg, p)
    save_registry(reg)
    sync_discovered_channels(reg)
    sync_channel_seeds(reg)

    qualified = sum(1 for v in reg.values() if (v.get("subscribers") or 0) >= MIN_SUBS)
    print(f"Merged {len(merged)} unique channels -> {out}")
    print(f"Registry channels: {len(reg)} qualified (>={MIN_SUBS} subs): {qualified}")
    print(f"Updated channel_seeds.json and discovered_channels.json with agent_specialty_tags")


def run_normalize() -> None:
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    log = logging.getLogger("normalize")
    root = Path(".")
    for pattern in ("probe_*.txt", "inspect*.txt", "expand_out.txt", "*.html"):
        for p in list(root.glob(pattern)):
            if p.name in ("lyzem_sample.html", "tgstat_sample.html", "sample_msg.html") or "probe_" in p.name:
                p.unlink(missing_ok=True)
    for p in (DATA / "agent_swarm" / "test.json", Path("probe_results.json")):
        if p.exists():
            p.unlink()
    reg: dict[str, dict] = {}
    disc_path = DISCOVERY_PATH
    if disc_path.exists():
        raw = json.loads(disc_path.read_text(encoding="utf-8"))
        for section in ("all", "qualified"):
            block = raw.get(section) or {}
            if isinstance(block, dict):
                for u, meta in block.items():
                    merge_into_registry(
                        reg,
                        u,
                        {
                            "title": meta.get("title"),
                            "subscribers": meta.get("subscribers"),
                            "specialty_tags": meta.get("agent_specialty_tags") or [],
                            "discovery_source": "discovered_channels",
                        },
                    )
    seeds_path = Path("channel_seeds.json")
    if seeds_path.exists():
        for s in json.loads(seeds_path.read_text(encoding="utf-8")):
            merge_into_registry(reg, s, {"discovery_source": "channel_seeds"})
    for path in sorted(DATA.glob("agent_*.json")):
        ingest_discovery_file(reg, path)
    swarm = DATA / "agent_swarm"
    if swarm.is_dir():
        for path in sorted(swarm.glob("*.json")):
            if path.name != "test.json":
                ingest_discovery_file(reg, path)
    import os

    from_scratch = os.environ.get("RERUN_FROM_SCRATCH") == "1"
    rescrape: list[str] = []
    stubs_deleted = 0
    partial_deleted = 0
    if POSTS_DIR.is_dir():
        for path in sorted(POSTS_DIR.glob("*.json")):
            u = path.stem.lower()
            try:
                posts = json.loads(path.read_bytes())
            except json.JSONDecodeError:
                rescrape.append(u)
                path.unlink(missing_ok=True)
                stubs_deleted += 1
                continue
            quality = classify_post_cache(posts)
            if quality == "stub" or (from_scratch and quality != "full"):
                path.unlink()
                if quality == "stub":
                    stubs_deleted += 1
                else:
                    partial_deleted += 1
                rescrape.append(u)
                if u in reg:
                    reg[u]["has_post_cache"] = False
                    reg[u]["post_cache_quality"] = "missing"
                continue
            if dedupe_file_extensions(posts):
                path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
            if u in reg:
                reg[u]["has_post_cache"] = True
                reg[u]["post_cache_quality"] = classify_post_cache(posts)
    for u, rec in reg.items():
        if rec.get("post_cache_quality") in ("stub", "missing", "partial"):
            rescrape.append(u)
    save_registry(reg)
    RESCRAPE_QUEUE_PATH.write_text(json.dumps(sorted(set(rescrape)), indent=2), encoding="utf-8")
    sync_discovered_channels(reg)
    sync_channel_seeds(reg)
    if (DATA / "agent_discoveries_merged.json").exists():
        for p in AGENT_FILES:
            if p.exists():
                p.unlink()
    log.info(
        "normalize done channels=%s rescrape=%s stubs_deleted=%s partial_deleted=%s",
        len(reg),
        len(set(rescrape)),
        stubs_deleted,
        partial_deleted,
    )
    print(
        json.dumps(
            {
                "channels": len(reg),
                "rescrape_queue": len(set(rescrape)),
                "stubs_deleted": stubs_deleted,
                "partial_deleted": partial_deleted,
                "from_scratch": from_scratch,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "normalize":
        run_normalize()
    else:
        try:
            main()
        except Exception:
            print("merge_agent_discoveries failed", file=sys.stderr)
            raise
