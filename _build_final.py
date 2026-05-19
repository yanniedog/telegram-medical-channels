import json,re
from pathlib import Path
BOOK=re.compile(r"books?|pdf|ebook",re.I)
EXAM=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step|qbank",re.I)
cache=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))["all"]
agent={e["username"].lower():e["subscribers_estimate"] for e in json.loads(Path("data/agent_discoveries_merged.json").read_text(encoding="utf-8"))}

def ok(u,m):
    s=m.get("subscribers") or agent.get(u,0)
    if s<2000: return False
    name=f"{u} {m.get('title') or ''}"
    if not BOOK.search(name): return False
    blob=f"{name} {m.get('description') or ''}"
    if EXAM.search(blob): return True
    if "medical book" in (m.get("title") or "").lower(): return True
    if u.startswith(("med","medical","freemedical","million_medical","neet","mbbs","usmle","plab","mrcp","fmge","pdf4","book")): return True
    return False

def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [("usmle","usmle"),("nbme","usmle"),("kaplan","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]:
        if k in b and t not in out: out.append(t)
    return out or ["mbbs"]

rows=[]
for u,m in cache.items():
    if not ok(u,m): continue
    s=m.get("subscribers") or agent.get(u,0)
    rows.append({"username":u,"subscribers_estimate":s,"specialty_tags":tags(m),
        "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})
rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
print("cache only",len(rows))

# fetch extra handles from lyzem not in cache
import httpx, time
from discover_channels import HEADERS, scrape_lyzem_page, fetch_channel_meta
extra=set()
qs=["usmle books pdf","plab books pdf","mrcp books pdf","mccqe books pdf","neet pg books pdf","mbbs books pdf","fmge books pdf","amc exam books pdf","medical board review pdf books"]
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for q in qs:
        for p in range(1,10):
            for h in scrape_lyzem_page(c,q,p):
                hl=h.lower()
                if hl not in cache and hl not in {r["username"] for r in rows}: extra.add(hl)
            time.sleep(0.2)
    for u in sorted(extra):
        m=fetch_channel_meta(c,u)
        if m.get("error"): continue
        s=m.get("subscribers") or 0
        if s<2000: continue
        name=f"{u} {m.get('title') or ''}"
        if not BOOK.search(name): continue
        blob=f"{name} {m.get('description') or ''}"
        if not (EXAM.search(blob) or "medical book" in (m.get("title") or "").lower() or u.startswith(("med","medical","freemedical","million_medical","neet","mbbs","usmle","plab","mrcp","fmge","pdf4"))):
            continue
        rows.append({"username":u,"subscribers_estimate":s,"specialty_tags":tags(m),
            "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})
        time.sleep(0.2)

seen=set(); final=[]
for r in rows:
    if r["username"] in seen: continue
    seen.add(r["username"]); final.append(r)
final.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
Path("data/agent_swarm/swarm_exams.json").write_text(json.dumps(final,ensure_ascii=False,indent=2),encoding="utf-8")
print("final",len(final))
for r in final: print(r["subscribers_estimate"],r["username"])
