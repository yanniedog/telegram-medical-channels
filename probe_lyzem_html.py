import httpx
from discover_channels import HEADERS
r = httpx.get("https://lyzem.com/search?q=books+pdf&page=1", headers=HEADERS, timeout=30, follow_redirects=True)
print("status", r.status_code, "len", len(r.text))
print(r.text[:2000])
