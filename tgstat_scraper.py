"""Scrape post samples from TGStat public channel pages."""
from __future__ import annotations

import re
import time

import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
PDF_EPUB = re.compile(r"\.(pdf|epub|djvu|mobi)\b", re.I)


def scrape_tgstat_channel(username: str) -> list[dict]:
    username = username.lstrip("@")
    posts: list[dict] = []
    for handle in (username, username.lower(), username.title()):
        url = f"https://tgstat.com/channel/@{handle}"
        try:
            r = httpx.get(url, headers=HEADERS, timeout=35, follow_redirects=True)
        except httpx.HTTPError:
            continue
        if r.status_code != 200:
            continue
        soup = BeautifulSoup(r.text, "lxml")

        for a in soup.select("a.file-anchor-wrapper[href*='ttttt.me']"):
            href = a.get("href", "")
            m = re.search(r"/(\d+)$", href)
            post_id = int(m.group(1)) if m else hash(href) % 10_000_000
            title_el = a.select_one(".file-title")
            fn = title_el.get_text(strip=True) if title_el else ""
            exts = []
            if PDF_EPUB.search(fn):
                exts.append(fn.rsplit(".", 1)[-1].lower())
            icon = a.select_one(".file-icon")
            if icon and "pdf" in " ".join(icon.get("class", [])):
                exts.append("pdf")
            if icon and "epub" in " ".join(icon.get("class", [])):
                exts.append("epub")
            post_text_el = a.find_parent(class_=re.compile("post|card|channel-post"))
            text = ""
            if post_text_el:
                pt = post_text_el.select_one(".post-text")
                text = pt.get_text(" ", strip=True) if pt else ""
            posts.append(
                {
                    "channel": username,
                    "post_id": post_id,
                    "datetime_utc": None,
                    "text": text or fn,
                    "views": None,
                    "is_forward": False,
                    "forward_from": None,
                    "has_direct_file": True,
                    "file_names": [fn] if fn else [],
                    "file_extensions": exts or (["pdf"] if ".pdf" in fn.lower() else []),
                    "external_urls": [],
                    "is_link_only_channel_promo": False,
                    "raw_links": [href],
                    "_source": "tgstat_sample",
                }
            )

        # text-only posts mentioning editions
        for block in soup.select(".post-text"):
            text = block.get_text(" ", strip=True)
            if len(text) < 15:
                continue
            if PDF_EPUB.search(text):
                continue
            if re.search(r"\b\d+(?:st|nd|rd|th)?\s+edition\b|\bedition\b", text, re.I):
                posts.append(
                    {
                        "channel": username,
                        "post_id": hash(text) % 10_000_000,
                        "datetime_utc": None,
                        "text": text,
                        "views": None,
                        "is_forward": False,
                        "forward_from": None,
                        "has_direct_file": False,
                        "file_names": [],
                        "file_extensions": [],
                        "external_urls": [],
                        "is_link_only_channel_promo": False,
                        "raw_links": [],
                        "_source": "tgstat_text_sample",
                    }
                )

        if posts:
            break
        time.sleep(0.4)

    seen: set[int] = set()
    uniq = []
    for p in posts:
        if p["post_id"] in seen:
            continue
        seen.add(p["post_id"])
        uniq.append(p)
    time.sleep(0.35)
    return uniq
