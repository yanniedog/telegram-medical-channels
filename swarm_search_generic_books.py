"""Search Lyzem for generic books/pdf/ebook channels with health potential."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

from discover_channels import HEADERS, TG_HANDLE, fetch_channel_meta, scrape_lyzem_page
from health_relevance import HEALTH_RE, health_relevance_score

USERNAME_SIGNAL = re.compile(r"books?|pdfs?|ebooks?", re.I)
OBVIOUS_MEDICAL = re.compile(
    r"med(?:ical|icine|ico)?|medic|pharm|surg|dent|nurs|clinic|hospital|usmle|mbbs|mrcp|plab|"
    r"pathol|radiol|cardio|neuro|psych|ophthal|gyn|obgyn|pediat|ortho|urolog|derma|"
    r"anesth|emerg|doctor|physician|mccqe|amc|nbme|kaplan|board|mcat|nclex|"
    r"pezeshki|tibb|doktor|hastane|klinik|medicina|medico|medizin",
    re.I,
)

LYZEM_QUERIES = [
    "books pdf", "pdf books", "ebook pdf", "free pdf books", "ebooks channel",
    "pdf library", "books channel", "book pdf telegram", "ebook library",
    "nutrition books pdf", "nutrition pdf", "anatomy books pdf", "anatomy pdf",
    "nursing books pdf", "nursing pdf", "physiotherapy pdf", "physio pdf",
    "veterinary books pdf", "vet books pdf", "wellness books pdf", "wellness pdf",
    "public health pdf", "health books pdf", "biology textbook pdf", "science books pdf",
    "psychology books pdf", "ayurved pdf", "diet books pdf", "pharmacology pdf books",
    "self help health pdf", "medical books pdf", "anesthesia books pdf",
    "dermatology books pdf", "ophthalmology books pdf", "dental books pdf",
    "engineering pdf books", "tamil books pdf", "hindi pdf books",
]

SEED_HANDLES = [
    "bookstoread_pdf", "pdf_books_hindi", "engineering_pdf_books", "tamil_books_pdf",
    "nutritionbook", "nutritionbooks", "anatomy_books_pdf", "phd_anatomy",
    "yasirnursingbooks", "nursingbookstore", "speedybook", "eBookRoom", "ebooks",
    "jpbookpdf", "ayurvedpdf", "fisioterapiapdf", "sdgtbookstore", "pdf4yo",
    "gastrointestinal_books", "neurobank_books", "cardiobooks", "orthopedic_book",
    "surgery_pdf_books", "radiologiaenpdf", "pediatric_pdfs", "psychiatrylibrarybooks",
    "newdermbooks", "ophthbooks", "critical_care_books", "kinobaxishbook",
    "tamilbookonline", "el3zonypdf", "novels_free_pdf",
]


def is_generic_username(username: str) -> bool:
    if not USERNAME_SIGNAL.search(username):
        return False
    if OBVIOUS_MEDICAL.search(username):
        return False
    return True


def classify_health(username: str, title: str, desc: str) -> tuple[str, int, list[str]]:
    score, reasons = health_relevance_score(username, title, desc)
    blob = f"{username} {title} {desc}"
    if "blocked_non_health" in reasons:
        return "exclude", score, reasons
    has_health = bool(HEALTH_RE.search(blob))
    if score >= 40 or (has_health and score >= 20):
        return "health_relevant", score, reasons
    if score >= 10 or has_health:
        return "possibly_health_relevant", score, reasons
    edu = re.search(
        r"science|biology|anatomy|nutrition|nursing|vet|physio|wellness|health|"
        r"psychology|pharmac|diet|medicine|clinical|therapy|rehab|textbook|"
        r"university|study|exam|student|ayurved|self.?help|wellbeing",
        blob, re.I,
    )
    if edu:
        return "possibly_health_relevant", score, reasons + ["edu_science_signal"]
    return "possibly_health_relevant", score, reasons


def main() -> None:
    out_path = Path("data/agent_swarm/swarm_generic_books_pdf.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    handles: list[str] = []

    for h in SEED_HANDLES:
        kl = h.lower()
        if kl not in seen and is_generic_username(h):
            seen.add(kl)
            handles.append(h)

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for q in LYZEM_QUERIES:
            for page in range(1, 8):
                batch = scrape_lyzem_page(client, q, page)
                if not batch:
                    break
                for h in batch:
                    kl = h.lower()
                    if kl not in seen and is_generic_username(h):
                        seen.add(kl)
                        handles.append(h)
                time.sleep(0.35)
            time.sleep(0.25)

        print(f"Generic handles to probe: {len(handles)}", flush=True)
        results: list[dict] = []
        for i, uname in enumerate(handles):
            meta = fetch_channel_meta(client, uname)
            if meta.get("error"):
                continue
            subs = meta.get("subscribers") or 0
            if subs < 2000:
                continue
            title = meta.get("title") or ""
            desc = meta.get("description") or ""
            label, score, reasons = classify_health(uname, title, desc)
            if label == "exclude":
                continue
            entry = {
                "username": uname.lower(),
                "title": title,
                "description": desc[:500] if desc else None,
                "subscribers_estimate": subs,
                "health_relevance_score": score,
                "health_match_reasons": reasons[:8],
                "source_url": f"https://tgstat.com/channel/@{uname}",
                "discovery_source": "lyzem_tgstat_generic_books_pdf",
            }
            if label == "health_relevant":
                entry["health_relevant"] = True
            else:
                entry["possibly_health_relevant"] = True
            results.append(entry)
            if (i + 1) % 20 == 0:
                print(f"  probed {i+1}/{len(handles)} qualified={len(results)}", flush=True)
            time.sleep(0.3)

    results.sort(key=lambda x: (-x.get("health_relevance_score", 0), -x["subscribers_estimate"]))
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    hr = sum(1 for r in results if r.get("health_relevant"))
    ph = sum(1 for r in results if r.get("possibly_health_relevant"))
    print(f"Wrote {out_path} total={len(results)} health_relevant={hr} possibly={ph}", flush=True)


if __name__ == "__main__":
    main()
