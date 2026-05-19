import json, re, time
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta, scrape_lyzem_page

MIN_SUBS = 2000
OUT = Path("data/agent_swarm/swarm_exams.json")
EXAM_RE = re.compile(r"\b(usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|ini-?cet|board\s*review|boards?\s+beyond|nbme|step\s*[123]|qbank|medical\s+board|exam\s+prep|pg\s+prep|medical\s+entrance)\b", re.I)
BOOK_PDF_RE = re.compile(r"\b(book|pdf|ebook|e-?book)\b", re.I)
LYZEM_QUERIES = ["USMLE books pdf telegram","USMLE pdf channel","PLAB books pdf telegram","MRCP books pdf telegram","MCCQE books pdf telegram","AMC exam books pdf telegram","NEET PG books pdf telegram","MBBS books pdf telegram","medical board review pdf telegram","FMGE books pdf telegram","USMLE step 1 books channel","PLAB MRCP pdf channel","NEET medical books pdf","Kaplan USMLE books telegram","medical exam prep pdf books"]
EXTRA_SEEDS = ["usmlebooks","usmlestore","usmlestep1233","usmlestep_1_2","medusmle","medicalusmle_videos","nbme_q","boards_beyonds","kaplan_atm","store_atm","mccqe","mccqe_1","plab_mrcp","mrcp2024","plabmaterials","plabbooks","mrcpbooks","mrcp_pdf","usmle_pdf","usmle_books","usmlestep1books","neetpgbooks","neet_books","neetpdf","mbbsbooks","mbbs_books_pdf","mbbsbookspdf","amcmcq","amcclinical","amcclinicalexamprep","amcmcqrecalls","medbookspdf","medical_ebook_pdfs","medbooksvn2","million_medical_books","medicalbooksstoress","medicalbooksstorea","pdf4yo","medpdf","medicalprep","freemedicalbooks","medical_free_ebooks","medicalbookspdfs","pdfmedbooks","usmle_premium_materials","usmle_materials","plab_materials","mccqe_exam","neet_pg_books","fmge_books","medical_board_books","medical_library25","medmaterialx","mmedicalbookss"]

def has_book_pdf_in_name(meta):
    blob = f"{meta.get('username','')} {meta.get('title','')}"
    return bool(BOOK_PDF_RE.search(blob))

def is_exam_relevant(meta):
    blob = " ".join(filter(None, [meta.get("username"), meta.get("title"), meta.get("description"), " ".join(meta.get("agent_specialty_tags") or []), " ".join(meta.get("specialty_tags") or [])]))
    return bool(EXAM_RE.search(blob))

def to_entry(meta):
    tags = []
    blob = f"{meta.get('username','')} {meta.get('title','')} {meta.get('description','')}".lower()
    for kw, tag in [("usmle","usmle"),("nbme","usmle"),("step 1","usmle"),("step 2","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]:
        if kw in blob and tag not in tags: tags.append(tag)
    if not tags: tags = ["exam_prep"]
    return {"username": meta["username"].lower(), "subscribers_estimate": meta.get("subscribers") or 0, "specialty_tags": tags, "has_direct_ebooks": bool(meta.get("has_web_preview")), "source_url": meta.get("link") or f"https://t.me/{meta['username']}", "title": meta.get("title")}

cached = {}
disc = Path("data/discovered_channels.json")
if disc.exists():
    raw = json.loads(disc.read_text(encoding="utf-8"))
    cached.update(raw.get("all") or {})
    cached.update(raw.get("qualified") or {})
merged = Path("data/agent_discoveries_merged.json")
if merged.exists():
    for e in json.loads(merged.read_text(encoding="utf-8")):
        u = e["username"].lower()
        if u not in cached:
            cached[u] = {"username": u, "subscribers": e.get("subscribers_estimate"), "title": None, "description": None, "link": e.get("source_url", f"https://t.me/{u}"), "agent_specialty_tags": e.get("specialty_tags", [])}

seen = set(cached.keys()) | {s.lower() for s in EXTRA_SEEDS}
OUT.parent.mkdir(parents=True, exist_ok=True)
meta_by_user = dict(cached)
with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
    for q in LYZEM_QUERIES:
        for page in range(1, 8):
            for h in scrape_lyzem_page(client, q, page):
                seen.add(h.lower())
            time.sleep(0.35)
        time.sleep(0.5)
    print("handles", len(seen))
    for i, uname in enumerate(sorted(seen)):
        cur = meta_by_user.get(uname, {})
        subs = cur.get("subscribers") or 0
        if subs >= MIN_SUBS and cur.get("title") and has_book_pdf_in_name(cur) and is_exam_relevant(cur):
            continue
        meta = fetch_channel_meta(client, uname)
        if meta.get("error"): continue
        meta_by_user[uname] = meta
        if (i+1) % 25 == 0:
            n = sum(1 for m in meta_by_user.values() if (m.get("subscribers") or 0) >= MIN_SUBS and has_book_pdf_in_name(m) and is_exam_relevant(m))
            print(i+1, "matched", n)
        time.sleep(0.28)

matched = [to_entry(m) for u,m in sorted(meta_by_user.items()) if (m.get("subscribers") or 0) >= MIN_SUBS and has_book_pdf_in_name(m) and is_exam_relevant(m)]
matched.sort(key=lambda x: (-x["subscribers_estimate"], x["username"]))
OUT.write_text(json.dumps(matched, ensure_ascii=False, indent=2), encoding="utf-8")
print("Wrote", OUT, "count=", len(matched))
