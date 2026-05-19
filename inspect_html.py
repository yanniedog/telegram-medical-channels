import re
import httpx
from bs4 import BeautifulSoup

html = httpx.get("https://t.me/s/Medbooksvn2", timeout=30).text
soup = BeautifulSoup(html, "lxml")
msg = soup.select_one(".tgme_widget_message_wrap")
if not msg:
    raise SystemExit("no msg")
# save snippet
with open("sample_msg.html", "w", encoding="utf-8") as f:
    f.write(str(msg))
# views
views = msg.select(".tgme_widget_message_views")
print("views elems", len(views), views[0].get_text() if views else None)
# files
for a in msg.select("a"):
    href = a.get("href", "")
    if "document" in href or ".pdf" in href.lower() or ".epub" in href.lower():
        print("link", href[:120], a.get_text(strip=True)[:80])
print("data-post", msg.select_one(".tgme_widget_message") and msg.select_one(".tgme_widget_message").get("data-post"))
