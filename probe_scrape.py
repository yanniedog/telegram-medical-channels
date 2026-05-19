import httpx
from discover_channels import HEADERS, scrape_lyzem_page, TG_HANDLE
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    hs = scrape_lyzem_page(c, "books pdf", 1)
    print("scrape", len(hs), hs[:15])
    r = c.get("https://lyzem.com/search?q=books+pdf&page=1", timeout=30)
    import re
    raw = [m.group(1) for m in TG_HANDLE.finditer(r.text)]
    print("raw", len(raw), raw[:15])
