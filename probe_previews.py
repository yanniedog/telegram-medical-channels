"""Probe which seed channels expose t.me/s/ post previews."""
import json
import time
import httpx
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

SEEDS = [
    "Medbooksvn2", "Million_medical_books", "MedicalBooksStoress", "medical_ebook_pdfs",
    "pdf4yo", "webofmedical", "freesurgerybooks28", "Internal_medicine_material",
    "Radiologist_Library", "radiologygoldenbooks", "MedicalLibraryMax", "medicalprep",
    "Medical_Free_Ebooks", "medpdf", "MedicalBooksStoreA", "MBS_MedicalBooksStore",
    "MedicalEbooksLibrary", "freemedicalbooks", "Million_Medical_Book", "medical_free_ebooks",
    "booksmedicospdf", "AMCMCQ", "AMCclinical", "amcclinicalexamprep",
]

def probe(username: str) -> dict:
    r = httpx.get(f"https://t.me/s/{username}", headers=HEADERS, timeout=30, follow_redirects=True)
    preview = "/s/" in str(r.url)
    posts = 0
    subs = None
    if preview and r.text:
        soup = BeautifulSoup(r.text, "lxml")
        posts = len(soup.select(".tgme_widget_message_wrap"))
        extra = soup.select_one(".tgme_channel_info_counter")
    # subscriber count from join page
    r2 = httpx.get(f"https://t.me/{username}", headers=HEADERS, timeout=30)
    soup2 = BeautifulSoup(r2.text, "lxml")
    for counter in soup2.select(".tgme_page_extra"):
        t = counter.get_text(" ", strip=True)
        if "subscriber" in t.lower() or "member" in t.lower():
            subs = t
            break
    return {
        "username": username,
        "preview_url": str(r.url),
        "has_preview": preview and posts > 0,
        "preview_posts": posts,
        "subscribers_text": subs,
        "status": r.status_code,
    }

if __name__ == "__main__":
    out = []
    for u in SEEDS:
        try:
            out.append(probe(u))
            print(out[-1])
        except Exception as e:
            out.append({"username": u, "error": str(e)})
        time.sleep(0.4)
    with open("probe_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
