import json
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta
import re
BOOK=re.compile(r"books?|pdf|ebook",re.I)
path=Path("data/agent_swarm/swarm_exams.json")
rows=json.loads(path.read_text(encoding="utf-8"))
seen={r["username"] for r in rows}
add=["neetpgmds","neetpgbooks","neet_books","neetpdf","plabbooks","mrcpbooks","mccqe_books","fmgebooks","mbbsbooks","million_medical_books","medbooksvn2","medical_ebook_pdfs","booksdana"]
def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [("usmle","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge")]:
        if k in b and t not in out: out.append(t)
    return out or ["mbbs"]
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for u in add:
        if u in seen: continue
        m=fetch_channel_meta(c,u)
        s=m.get("subscribers") or 0
        if s<2000: continue
        if not BOOK.search(f"{u} {m.get('title') or ''}"): continue
        rows.append({"username":u,"subscribers_estimate":s,"specialty_tags":tags(m),
            "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})
        seen.add(u)
rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
path.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print(len(rows))
