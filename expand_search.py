import json, re, time
from pathlib import Path
import httpx
from discover_channels import HEADERS, scrape_lyzem_page, fetch_channel_meta

USERNAME = re.compile(r"books?|pdfs?|ebooks?", re.I)
MED = re.compile(r"med(?:ical|icine|ico)?|medic|pharm|surg|dent|clinic|hospital|usmle|mbbs|mrcp|plab|pathol|radiol|cardio|neuro|psych|ophthal|gyn|obgyn|pediat|ortho|urolog|derma|anesth|emerg|doctor|physician|mccqe|amc|nbme|pezeshki|medicina|medico", re.I)

extra_queries = [
    "library pdf", "pdf store", "pdf hub", "book store pdf", "free ebooks",
    "textbook pdf", "study pdf", "university books pdf", "college books pdf",
    "science pdf", "biology pdf books", "chemistry books pdf", "pharmacy books pdf",
    "diet pdf", "fitness books pdf", "yoga books pdf", "mental health books pdf",
    "counseling books pdf", "social work books pdf", "midwifery books pdf",
    "paramedic books pdf", "occupational therapy pdf", "speech therapy pdf",
    "optometry books pdf", "chiropractic pdf", "homeopathy books pdf",
    "herbal medicine pdf", "traditional medicine pdf", "first aid pdf",
    "emergency care pdf", "anatomy atlas pdf", "histology pdf", "microbiology pdf",
    "biochemistry pdf", "epidemiology pdf", "health science pdf",
    "libros pdf", "livres pdf", "kitap pdf", "buch pdf",
]

seen = set()
candidates = []
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for q in extra_queries:
        for page in range(1, 6):
            batch = scrape_lyzem_page(c, q, page)
            if not batch: break
            for h in batch:
                kl = h.lower()
                if kl in seen: continue
                seen.add(kl)
                if not USERNAME.search(h): continue
                if MED.search(h): continue
                candidates.append(h)
        time.sleep(0.2)

print("new candidates", len(candidates))
qualified = []
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for h in candidates[:80]:
        m = fetch_channel_meta(c, h)
        subs = m.get("subscribers") or 0
        if subs >= 2000:
            qualified.append((h, subs, m.get("title","")[:40]))
        time.sleep(0.25)
print("qualified 2k+", len(qualified))
for q in qualified[:50]:
    print(q)
