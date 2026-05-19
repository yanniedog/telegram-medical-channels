import httpx
from bs4 import BeautifulSoup

r = httpx.get("https://t.me/s/Medbooksvn2", timeout=30, follow_redirects=True)
print("status", r.status_code, "len", len(r.text))
s = BeautifulSoup(r.text, "lxml")
posts = s.select(".tgme_widget_message_wrap")
print("posts", len(posts))
for p in posts[:2]:
    print("---")
    print(p.get_text(" ", strip=True)[:300])
