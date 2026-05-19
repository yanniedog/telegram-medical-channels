"""Scrape public Telegram channel previews (t.me/s) with pagination."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

VIEWS_RE = re.compile(r"^([\d.]+)([KkMm])?$")


def parse_views(text: str | None) -> int | None:
    if not text:
        return None
    text = text.strip().replace(",", "")
    m = VIEWS_RE.match(text)
    if not m:
        return None
    v = float(m.group(1))
    s = (m.group(2) or "").upper()
    if s == "K":
        v *= 1000
    elif s == "M":
        v *= 1_000_000
    return int(v)


@dataclass
class ScrapedPost:
    channel: str
    post_id: int
    datetime_utc: str | None
    text: str
    views: int | None
    is_forward: bool
    forward_from: str | None
    has_direct_file: bool
    file_names: list[str]
    file_extensions: list[str]
    external_urls: list[str]
    is_link_only_channel_promo: bool
    raw_links: list[str] = field(default_factory=list)


def _parse_datetime(time_el) -> str | None:
    if not time_el:
        return None
    dt = time_el.get("datetime")
    return dt


def parse_message_wrap(wrap, channel: str) -> ScrapedPost | None:
    root = wrap.select_one(".tgme_widget_message")
    if not root:
        return None
    data_post = root.get("data-post") or ""
    if "/" not in data_post:
        return None
    _, pid = data_post.split("/", 1)
    try:
        post_id = int(pid)
    except ValueError:
        return None

    text_el = wrap.select_one(".tgme_widget_message_text")
    text = text_el.get_text("\n", strip=True) if text_el else ""

    views_el = wrap.select_one(".tgme_widget_message_views")
    views = parse_views(views_el.get_text(strip=True) if views_el else None)

    time_el = wrap.select_one(".tgme_widget_message_date time")
    dt = _parse_datetime(time_el)

    forward_el = wrap.select_one(".tgme_widget_message_forwarded_from")
    forward_from = forward_el.get_text(strip=True) if forward_el else None
    is_forward = bool(forward_el)

    file_names: list[str] = []
    extensions: list[str] = []
    for doc in wrap.select(".tgme_widget_message_document_wrap"):
        title = doc.select_one(".tgme_widget_message_document_title")
        if title:
            fn = title.get_text(strip=True)
            file_names.append(fn)
            if "." in fn:
                extensions.append(fn.rsplit(".", 1)[-1].lower())

    for a in wrap.select("a"):
        href = a.get("href") or ""
        label = a.get_text(strip=True)
        if ".pdf" in href.lower() or ".pdf" in label.lower():
            if label and label not in file_names:
                file_names.append(label)
            extensions.append("pdf")
        elif ".epub" in href.lower() or ".epub" in label.lower():
            if label:
                file_names.append(label)
            extensions.append("epub")
        elif ".ppt" in href.lower() or ".pptx" in label.lower():
            extensions.append("ppt" if "pptx" not in href.lower() else "pptx")
        elif ".apk" in href.lower():
            extensions.append("apk")
        elif ".mp3" in href.lower() or ".m4a" in href.lower():
            extensions.append("audio")
        elif any(x in href.lower() for x in (".mp4", ".mkv", ".avi", "youtube.com", "youtu.be")):
            extensions.append("video")

    external_urls = []
    raw_links = []
    for a in wrap.select(".tgme_widget_message_text a"):
        href = a.get("href") or ""
        raw_links.append(href)
        if href and "t.me/" not in href and "telegram.me" not in href:
            external_urls.append(href)

    has_direct_file = bool(file_names) or any(
        ext in extensions for ext in ("pdf", "epub", "djvu", "mobi", "azw3", "cbz", "cbr")
    )

    # link-only: external catalog / other-channel promo without Telegram-hosted file
    link_only = not has_direct_file and (
        bool(external_urls)
        or (
            not extensions
            and bool(re.findall(r"t\.me/\+?[A-Za-z0-9_]+", text))
            and not is_forward
        )
    )

    return ScrapedPost(
        channel=channel,
        post_id=post_id,
        datetime_utc=dt,
        text=text,
        views=views,
        is_forward=is_forward,
        forward_from=forward_from,
        has_direct_file=has_direct_file,
        file_names=file_names,
        file_extensions=list(dict.fromkeys(extensions)),
        external_urls=external_urls,
        is_link_only_channel_promo=link_only,
        raw_links=raw_links,
    )


def scrape_channel(username: str, max_pages: int = 500, delay: float = 0.45) -> list[ScrapedPost]:
    username = username.lstrip("@")
    posts: list[ScrapedPost] = []
    seen_ids: set[int] = set()
    before: int | None = None

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=35) as client:
        for _ in range(max_pages):
            url = f"https://t.me/s/{username}"
            if before is not None:
                url += f"?before={before}"
            r = client.get(url)
            if "/s/" not in str(r.url) or r.status_code != 200:
                break
            soup = BeautifulSoup(r.text, "lxml")
            wraps = soup.select(".tgme_widget_message_wrap")
            if not wraps:
                break
            page_ids: list[int] = []
            for w in wraps:
                p = parse_message_wrap(w, username)
                if not p or p.post_id in seen_ids:
                    continue
                seen_ids.add(p.post_id)
                page_ids.append(p.post_id)
                posts.append(p)
            if not page_ids:
                break
            new_before = min(page_ids)
            if before is not None and new_before >= before:
                break
            before = new_before
            time.sleep(delay)
    return posts


def save_posts(username: str, posts: list[ScrapedPost], base: Path = Path("data/posts")) -> Path:
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{username.lower()}.json"
    path.write_text(
        json.dumps([asdict(p) for p in posts], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


if __name__ == "__main__":
    import sys

    ch = sys.argv[1] if len(sys.argv) > 1 else "Medbooksvn2"
    result = scrape_channel(ch, max_pages=30)
    print(ch, "posts", len(result))
    save_posts(ch, result)
