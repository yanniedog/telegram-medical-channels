"""Scrape recent post text from Telemetr channel detail pages."""
from __future__ import annotations

import re
import time

import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# Known Telemetr slugs (username -> path suffix)
TELEMETR_SLUGS = {
    "medicalbooksstoress": "1181107354-medicalbooksstoress",
    "million_medical_books": "1251150049-million_medical_books",
    "medicalbooksstorea": "1914416855-medical_booksy",
}


def scrape_telemetr_channel(username: str) -> list[dict]:
    username = username.lstrip("@")
    key = username.lower()
    slug = TELEMETR_SLUGS.get(key)
    posts: list[dict] = []
    urls = []
    if slug:
        urls.append(f"https://telemetr.io/en/channels/{slug}")
    urls.append(f"https://telemetr.io/en/channels?search=@{username}")

    for url in urls:
        try:
            r = httpx.get(url, headers=HEADERS, timeout=40, follow_redirects=True)
        except httpx.HTTPError:
            continue
        if r.status_code != 200:
            continue
        soup = BeautifulSoup(r.text, "lxml")
        # Post cards often in channel posts section
        for block in soup.select("[class*='post'], article, .channel-post, li"):
            text = block.get_text(" ", strip=True)
            if len(text) < 20:
                continue
            if not re.search(
                r"\.(pdf|epub)|edition|USMLE|medicine|surgery|radiology|@|MP4|Videos",
                text,
                re.I,
            ):
                continue
            if "subscriber" in text.lower() and len(text) < 80:
                continue
            exts = []
            if re.search(r"\.pdf\b", text, re.I):
                exts.append("pdf")
            if re.search(r"\.epub\b", text, re.I):
                exts.append("epub")
            if re.search(r"\bmp4\b|video", text, re.I):
                exts.append("video")
            if re.search(r"\bapk\b", text, re.I):
                exts.append("apk")
            if re.search(r"pptx?", text, re.I):
                exts.append("ppt")
            views = None
            vm = re.search(r"\b([\d.,]+)\s*([KkMm])?\b", text)
            # view counts at end of telemetr cards are unreliable; skip
            posts.append(
                {
                    "channel": username,
                    "post_id": hash(text[:200]) % 10_000_000,
                    "datetime_utc": None,
                    "text": text[:800],
                    "views": views,
                    "is_forward": "repost" in text.lower(),
                    "forward_from": None,
                    "has_direct_file": bool(exts) or bool(re.search(r"\bPDFs?\b", text)),
                    "file_names": [],
                    "file_extensions": exts,
                    "external_urls": re.findall(r"https?://\S+", text),
                    "is_link_only_channel_promo": bool(re.search(r"Contact us : @", text)),
                    "raw_links": [],
                    "_source": "telemetr_sample",
                }
            )
        if posts:
            break
        time.sleep(0.5)

    seen = set()
    uniq = []
    for p in posts:
        k = p["text"][:100]
        if k in seen:
            continue
        seen.add(k)
        uniq.append(p)
    return uniq[:60]
