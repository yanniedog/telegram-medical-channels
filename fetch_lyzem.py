import httpx, re
from discover_channels import HEADERS, TG_HANDLE
r = httpx.get("https://lyzem.com/search?q=books+pdf&page=1", headers=HEADERS, timeout=30, follow_redirects=True)
open("lyzem_sample.html","w",encoding="utf-8").write(r.text)
print("len", len(r.text), "status", r.status_code)
raw = [m.group(1) for m in TG_HANDLE.finditer(r.text)]
print("handles", len(raw), raw)
