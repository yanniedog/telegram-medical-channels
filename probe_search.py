import json, re, time
from pathlib import Path
import httpx
from discover_channels import HEADERS, scrape_lyzem_page, fetch_channel_meta, TG_HANDLE
from urllib.parse import quote_plus

queries = ["books pdf", "pdf books", "ebook pdf", "free pdf books"]
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for q in queries:
        hs = scrape_lyzem_page(c, q, 1)
        print(q, len(hs), hs[:8])
        url = f"https://tgstat.com/search?q={quote_plus(q)}&type=channel"
        r = c.get(url, timeout=30)
        tg = [m.group(1) for m in TG_HANDLE.finditer(r.text)]
        print(" tgstat", r.status_code, len(tg), tg[:8])
        time.sleep(0.5)
