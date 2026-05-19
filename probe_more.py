import httpx, re
from discover_channels import HEADERS, TG_HANDLE
for url in [
    "https://tgstat.com/channels/search?query=books+pdf",
    "https://tgstat.ru/en/channels/search?query=pdf+books",
    "https://lyzem.com/search?q=nutrition+books+pdf&page=1",
    "https://lyzem.com/search?q=anatomy+pdf&page=1",
    "https://lyzem.com/search?q=nursing+books+pdf&page=1",
]:
    r = httpx.get(url, headers=HEADERS, timeout=30, follow_redirects=True)
    hs = [m.group(1) for m in TG_HANDLE.finditer(r.text)]
    print(url.split("?")[0].split("/")[-1], r.status_code, len(hs), hs[:6])
