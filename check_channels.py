import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
channels = [
    "MedicalBooksStoress",
    "medpdf",
    "Medical_Free_Ebooks",
    "freemedicalbooks",
    "MedicalBooksStoreA",
    "MBS_MedicalBooksStore",
    "Million_medical_books",
]
for u in channels:
    r = httpx.get(f"https://t.me/s/{u}", headers=HEADERS, timeout=30)
    s = BeautifulSoup(r.text, "lxml")
    n = len(s.select(".tgme_widget_message_wrap"))
    print(u, r.status_code, len(r.text), n)
