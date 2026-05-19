import httpx, re
from discover_channels import HEADERS
from bs4 import BeautifulSoup
r = httpx.get("https://tgstat.com/search?q=books+pdf&type=channel", headers=HEADERS, timeout=30, follow_redirects=True)
print("status", r.status_code, "len", len(r.text))
for pat in [r"t\.me/[\w]+", r"@[\w]+", r"/channel/@", r"href=\"[^\"]+channel"]:
    m = re.findall(pat, r.text[:50000])
    print(pat, len(m), m[:5])
soup = BeautifulSoup(r.text, "lxml")
links = [a.get("href") for a in soup.select("a[href*='channel']")[:20]]
print("links", links)
