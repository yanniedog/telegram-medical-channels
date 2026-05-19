import httpx, re
from discover_channels import HEADERS
r = httpx.get("https://lyzem.com/search?q=books+pdf&page=1", headers=HEADERS, timeout=30, follow_redirects=True)
for pat in [r"t\.me/[A-Za-z0-9_]+", r"@[A-Za-z0-9_]{4,}", r"username", r"channel", r"href=\"[^\"]+\""]:
    ms = re.findall(pat, r.text)
    print(pat, len(ms))
    if ms: print(" sample", ms[:8])
# look for json data
for m in re.finditer(r"telegram\.me|t\.me|@\\w+", r.text):
    pass
idx = r.text.find("t.me")
print("first t.me idx", idx)
if idx>=0: print(r.text[idx-100:idx+200])
idx2 = r.text.lower().find("book")
print("book contexts:")
for m in re.finditer(r".{0,40}book.{0,40}", r.text, re.I):
    s = m.group(0)
    if "icon" not in s.lower() and "stylesheet" not in s.lower():
        print(repr(s[:100]))
        break
