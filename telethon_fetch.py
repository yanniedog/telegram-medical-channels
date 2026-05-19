"""
Optional: fetch full channel history via Telethon (requires API credentials).

Create .env with TELEGRAM_API_ID and TELEGRAM_API_HASH from https://my.telegram.org
First run will prompt for phone login and create telethon_session.session
"""
from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
SESSION = os.getenv("TELEGRAM_SESSION", "telethon_session")


async def fetch_channel(client, username: str, limit: int | None = None) -> list[dict]:
    from channel_scraper import ScrapedPost  # noqa: F401

    posts = []
    async for msg in client.iter_messages(username, limit=limit):
        if not msg:
            continue
        text = msg.message or ""
        file_names = []
        exts = []
        if msg.document:
            fn = getattr(msg.file, "name", None) or "document"
            file_names.append(fn)
            if "." in fn:
                exts.append(fn.rsplit(".", 1)[-1].lower())
        posts.append(
            {
                "channel": username,
                "post_id": msg.id,
                "datetime_utc": msg.date.isoformat() if msg.date else None,
                "text": text,
                "views": msg.views,
                "is_forward": bool(msg.forward),
                "forward_from": None,
                "has_direct_file": bool(msg.document or msg.media),
                "file_names": file_names,
                "file_extensions": exts,
                "external_urls": [],
                "is_link_only_channel_promo": False,
                "raw_links": [],
                "_source": "telethon",
            }
        )
    return posts


async def main() -> None:
    if not API_ID or not API_HASH:
        raise SystemExit("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")

    from telethon import TelegramClient

    discovery = json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))
    qualified = discovery.get("qualified", {})
    out_dir = Path("data/posts")
    out_dir.mkdir(parents=True, exist_ok=True)

    async with TelegramClient(SESSION, int(API_ID), API_HASH) as client:
        for key, meta in qualified.items():
            uname = meta.get("username") or key
            path = out_dir / f"{uname.lower()}.json"
            if path.exists() and path.stat().st_size > 50_000:
                print("skip", uname)
                continue
            print("fetch", uname)
            posts = await fetch_channel(client, uname)
            path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
            print(" ", len(posts), "posts")

    print("Done. Run: python build_from_cache.py")


if __name__ == "__main__":
    asyncio.run(main())
