import httpx
from bs4 import BeautifulSoup

html = httpx.get("https://t.me/s/medical_free_ebooks", timeout=30).text
soup = BeautifulSoup(html, "lxml")
for i, msg in enumerate(soup.select(".tgme_widget_message_wrap")[:5]):
    root = msg.select_one(".tgme_widget_message")
    post_id = root.get("data-post") if root else "?"
    views = msg.select_one(".tgme_widget_message_views")
    v = views.get_text(strip=True) if views else ""
    text = msg.get_text(" ", strip=True)[:120]
    files = []
    for a in msg.select("a.document, a[href*='document']"):
        files.append(a.get_text(strip=True)[:60])
    for a in msg.select(".tgme_widget_message_document_wrap a"):
        files.append(a.get_text(strip=True)[:60])
    print(i, post_id, v, "files", files, "text", text.replace("\n", " "))
