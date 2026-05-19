import json, re, time
from pathlib import Path
import httpx
from discover_channels import HEADERS, scrape_lyzem_page, fetch_channel_meta
from health_relevance import health_relevance_score, HEALTH_RE

USERNAME = re.compile(r"books?|pdfs?|ebooks?", re.I)
OBVIOUS = re.compile(
    r"med(?:ical|icine|ico)?|medic|pharm|surg|dent|clinic|hospital|usmle|mbbs|mrcp|plab|"
    r"pathol|radiol|cardio|neuro|psych|ophthal|gyn|obgyn|pediat|ortho|urolog|derma|"
    r"anesth|emerg|doctor|physician|mccqe|amc|nbme|pezeshki|medicina|medico", re.I)

queries = [
    "books pdf", "pdf books", "ebook", "ebooks", "free pdf", "pdf library", "book store",
    "nutrition pdf", "anatomy pdf", "nursing pdf", "physio pdf", "vet pdf", "veterinary pdf",
    "wellness pdf", "health pdf", "biology pdf", "science pdf", "psychology pdf",
    "ayurved pdf", "yoga pdf", "diet pdf", "pharmacy pdf", "dental pdf", "midwifery pdf",
    "paramedic pdf", "therapy pdf", "rehab pdf", "public health pdf", "epidemiology pdf",
    "microbiology pdf", "biochemistry pdf", "histology pdf", "optometry pdf", "chiropractic pdf",
    "homeopathy pdf", "herbal pdf", "first aid pdf", "emergency pdf", "self help pdf",
    "libros pdf", "kitap pdf", "livres pdf", "punjabi pdf books", "hindi pdf books",
    "tamil pdf books", "arabic pdf books", "persian pdf books", "russian pdf books",
    "engineering pdf", "law pdf books", "business pdf books", "novel pdf", "comic pdf",
    "anatomy books", "nursing books", "nutrition books", "vet books", "physiotherapy books",
    "speedy book", "ebook room", "book club pdf", "pdf hub", "pdf world", "pdf zone",
]

seeds = [
    "eBookRoom", "bookstoread_pdf", "pdf_books_hindi", "engineering_pdf_books", "tamil_books_pdf",
    "nutritionbook", "nutritionbooks", "anatomy_books_pdf", "phd_anatomy", "yasirnursingbooks",
    "nursingbookstore", "ayurvedpdf", "novels_free_pdf", "bookstore_gilan", "el3zonypdf",
    "audiobo0ok", "pdf_kutib", "relation4ips", "ecrocks", "fam_06", "draftabahmed",
    "neurobank_books", "cardiobooks", "orthopedic_book", "surgery_pdf_books", "pediatric_pdfs",
    "radiologiaenpdf", "psychiatrylibrarybooks", "anatomy_books", "nursing_books_pdf",
    "publichealthbooks", "wellnessbooks", "biologybooks_pdf", "sciencebooks_pdf",
    "pharmacybookspdf", "dentalbookspdf", "midwiferybooks", "paramedicbooks",
]

seen=set(); handles=[]
for h in seeds:
    if USERNAME.search(h) and h.lower() not in seen:
        seen.add(h.lower()); handles.append(h)

with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for q in queries:
        for page in range(1, 8):
            batch = scrape_lyzem_page(c, q, page)
            if not batch: break
            for h in batch:
                kl=h.lower()
                if kl in seen: continue
                if not USERNAME.search(h): continue
                seen.add(kl); handles.append(h)
        time.sleep(0.15)

print("total handles", len(handles), flush=True)
existing = {x["username"] for x in json.loads(Path("data/agent_swarm/swarm_generic_books_pdf.json").read_text(encoding="utf-8"))}
new_rows=[]
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for i,h in enumerate(handles):
        if h.lower() in existing: continue
        if OBVIOUS.search(h): continue
        m = fetch_channel_meta(c, h)
        if m.get("error"): continue
        subs = m.get("subscribers") or 0
        if subs < 2000: continue
        title = m.get("title") or ""
        desc = m.get("description") or ""
        score, reasons = health_relevance_score(h, title, desc)
        if "blocked_non_health" in reasons: continue
        label = "health_relevant" if score >= 40 or (HEALTH_RE.search(f"{h} {title} {desc}") and score >= 20) else "possibly_health_relevant"
        if score < 10 and not HEALTH_RE.search(f"{title} {desc}"):
            label = "possibly_health_relevant"
        new_rows.append((h, subs, score, label, title[:35]))
        if (i+1)%30==0: print(f" probed {i+1} new={len(new_rows)}", flush=True)
        time.sleep(0.25)

print("new qualified", len(new_rows))
for r in sorted(new_rows, key=lambda x:-x[2])[:30]:
    print(r)
