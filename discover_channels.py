"""Discover medical book Telegram channels via Lyzem search + seed lists."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
QUERIES = [
    "medical books pdf",
    "medical ebooks",
    "medical library pdf",
    "mbbs books pdf",
    "usmle books pdf",
    "surgery books pdf",
    "radiology books pdf",
    "medical epub",
    "free medical books",
    "medical textbook pdf",
    "anatomy books pdf",
    "pharmacology books pdf",
    "medical books telegram",
    "ebook medicine pdf",
    "AMC medical books",
]

SEED_USERNAMES = [
    "Medbooksvn2", "Million_medical_books", "MedicalBooksStoress", "MedicalBooksStoreA",
    "medical_ebook_pdfs", "pdf4yo", "webofmedical", "freesurgerybooks28",
    "Internal_medicine_material", "Radiologist_Library", "radiologygoldenbooks",
    "MedicalLibraryMax", "medicalprep", "Medical_Free_Ebooks", "medpdf",
    "MBS_MedicalBooksStore", "MedicalEbooksLibrary", "freemedicalbooks",
    "Million_Medical_Book", "medical_free_ebooks", "booksmedicospdf",
    "AMCMCQ", "AMCclinical", "amcclinicalexamprep", "medicalusmle_videos",
    "medical_book772", "Medical_Books_Storess", "pezeshkibooks", "medical_e_books",
    "pdfmedbooks", "medicalbookshare", "medicalbookspdfs", "medicinestore",
    "tushar_medicalbooks", "girishparmarmld", "medicalegypt", "medical_free_ebooks",
    "MedicalBooksStoress", "dtunewsmedicine", "NBME_Q", "Store_ATM", "MedstudyVideos",
    "MCCQE_1", "Boards_BeyondS", "Kaplan_ATM", "med_material", "medusmle",
]

TG_HANDLE = re.compile(
    r"(?:https?://)?(?:t\.me|telegram\.me)/([A-Za-z0-9_]{4,})(?:/|\?|[\"'\s<>]|$)",
    re.I,
)


def parse_subscribers(text: str | None) -> int | None:
    if not text:
        return None
    t = text.lower().replace("\xa0", " ").replace(",", "")
    # Telegram uses thin/regular spaces as thousands separators: "59 208 subscribers"
    t = re.sub(r"(?<=\d)\s+(?=\d)", "", t)
    m = re.search(r"([\d.]+)\s*([km])?\s*(subscriber|member)", t)
    if not m:
        return None
    val = float(m.group(1))
    suffix = (m.group(2) or "").lower()
    if suffix == "k":
        val *= 1000
    elif suffix == "m":
        val *= 1_000_000
    return int(val)


def fetch_channel_meta(client: httpx.Client, username: str) -> dict:
    username = username.lstrip("@")
    try:
        r = client.get(f"https://t.me/{username}", timeout=25)
    except httpx.HTTPError as e:
        return {"username": username, "error": str(e)}
    if r.status_code != 200:
        return {"username": username, "error": f"http {r.status_code}"}
    soup = BeautifulSoup(r.text, "lxml")
    title_el = soup.select_one(".tgme_page_title")
    desc_el = soup.select_one(".tgme_page_description")
    subs_text = None
    for extra in soup.select(".tgme_page_extra, .tgme_channel_info_counter"):
        t = extra.get_text(" ", strip=True)
        if re.search(r"subscriber|member", t, re.I):
            subs_text = t
            break
    if not subs_text:
        extra = soup.select_one(".tgme_page_extra")
        subs_text = extra.get_text(" ", strip=True) if extra else None
    # preview check
    r2 = client.get(f"https://t.me/s/{username}", timeout=25)
    has_preview = "/s/" in str(r2.url) and len(r2.text) > 5000
    preview_posts = 0
    if has_preview:
        preview_posts = len(BeautifulSoup(r2.text, "lxml").select(".tgme_widget_message_wrap"))
    return {
        "username": username,
        "title": title_el.get_text(strip=True) if title_el else None,
        "description": desc_el.get_text(" ", strip=True) if desc_el else None,
        "subscribers_text": subs_text,
        "subscribers": parse_subscribers(subs_text),
        "has_web_preview": has_preview and preview_posts > 0,
        "preview_posts_on_page": preview_posts,
        "link": f"https://t.me/{username}",
    }


def scrape_lyzem_page(client: httpx.Client, query: str, page: int = 1) -> list[str]:
    url = f"https://lyzem.com/search?q={quote_plus(query)}&page={page}"
    try:
        r = client.get(url, timeout=30)
    except httpx.HTTPError:
        return []
    if r.status_code != 200:
        return []
    handles = []
    for m in TG_HANDLE.finditer(r.text):
        h = m.group(1)
        if h.lower() not in ("joinchat", "s", "share", "addstickers", "proxy"):
            handles.append(h)
    return handles


def main() -> None:
    out_path = Path("data/discovered_channels.json")
    out_path.parent.mkdir(exist_ok=True)
    seen: set[str] = set()
    channels: dict[str, dict] = {}
    seeds_path = Path("channel_seeds.json")
    if seeds_path.exists():
        for u in json.loads(seeds_path.read_text(encoding="utf-8")):
            seen.add(u.lower())

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for u in SEED_USERNAMES:
            seen.add(u.lower())

        for q in QUERIES:
            for page in range(1, 11):
                handles = scrape_lyzem_page(client, q, page)
                if not handles:
                    break
                for h in handles:
                    seen.add(h.lower())
                time.sleep(0.6)
            time.sleep(0.8)

        print(f"Unique handles from discovery: {len(seen)}")
        for i, uname in enumerate(sorted(seen, key=str.lower)):
            meta = fetch_channel_meta(client, uname)
            if meta.get("error"):
                continue
            channels[uname.lower()] = meta
            if (i + 1) % 10 == 0:
                q = sum(1 for c in channels.values() if (c.get("subscribers") or 0) >= 2000)
                print(f"  meta {i+1}/{len(seen)} qualified(>=2k)={q}")
            time.sleep(0.35)

    qualified = {k: v for k, v in channels.items() if (v.get("subscribers") or 0) >= 2000}
    out_path.write_text(json.dumps({"all": channels, "qualified": qualified}, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} qualified={len(qualified)} total_meta={len(channels)}")


if __name__ == "__main__":
    main()
