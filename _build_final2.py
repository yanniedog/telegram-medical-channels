import json,re,time
from pathlib import Path
import httpx
from discover_channels import HEADERS, scrape_lyzem_page, fetch_channel_meta

BOOK=re.compile(r"books?|pdf|ebook",re.I)
MED_EXAM=re.compile(r"medical|medic|usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step\s*[123]|qbank|exam|pg\s*prep|anatomy|physiology|pathol|surg|cardio|pediat|dent|pharm|radiol|anesth|ophth|gyn|neuro|ortho|licensing|student",re.I)

def book_name(u,m):
    return bool(BOOK.search(f"{u} {m.get('title') or ''}"))

def med_exam(u,m):
    blob=f"{u} {m.get('title') or ''} {m.get('description') or ''}"
    return bool(MED_EXAM.search(blob))

def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [("usmle","usmle"),("nbme","usmle"),("kaplan","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]:
        if k in b and t not in out: out.append(t)
    return out or ["mbbs"]

cache=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))["all"]
agent={e["username"].lower():e["subscribers_estimate"] for e in json.loads(Path("data/agent_discoveries_merged.json").read_text(encoding="utf-8"))}

rows=[]
for u,m in cache.items():
    s=m.get("subscribers") or agent.get(u,0)
    if s<2000 or not book_name(u,m) or not med_exam(u,m): continue
    rows.append({"username":u,"subscribers_estimate":s,"specialty_tags":tags(m),
        "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})

seen={r["username"] for r in rows}
extra=set()
for q in ["usmle books pdf telegram","plab books pdf","mrcp books pdf","mccqe books pdf","neet pg books pdf","mbbs books pdf","fmge books pdf","amc exam books pdf","medical board review pdf","first aid usmle pdf","kaplan usmle books","medical exam books pdf","plab mrcp books pdf"]:
    pass

with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for q in ["usmle books pdf telegram","plab books pdf","mrcp books pdf","mccqe books pdf","neet pg books pdf","mbbs books pdf","fmge books pdf","amc exam books pdf","medical board review pdf","first aid usmle pdf","kaplan usmle books","medical exam books pdf","plab mrcp books pdf","usmle step 1 pdf books"]:
        for p in range(1,10):
            for h in scrape_lyzem_page(c,q,p):
                hl=h.lower()
                if hl not in seen: extra.add(hl)
            time.sleep(0.2)
    for u in sorted(extra):
        m=fetch_channel_meta(c,u)
        if m.get("error"): continue
        s=m.get("subscribers") or 0
        if s<2000 or not book_name(u,m) or not med_exam(u,m): continue
        if u in seen: continue
        seen.add(u)
        rows.append({"username":u,"subscribers_estimate":s,"specialty_tags":tags(m),
            "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})
        time.sleep(0.2)

rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
Path("data/agent_swarm/swarm_exams.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print("COUNT",len(rows))
