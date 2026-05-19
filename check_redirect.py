import httpx

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
for u in ["Medbooksvn2", "MedicalBooksStoress"]:
    r = httpx.get(f"https://t.me/s/{u}", headers=HEADERS, timeout=30, follow_redirects=True)
    print(u, r.status_code, str(r.url), len(r.text), r.history)
