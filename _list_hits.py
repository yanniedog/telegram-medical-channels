import json,re
from pathlib import Path
BOOK=re.compile(r"pdf|ebook|\bbooks?\b|bookstore|bookspdf|_books|books_",re.I)
EXAM=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step|qbank",re.I)
cache=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))["all"]
agent={e["username"].lower():e["subscribers_estimate"] for e in json.loads(Path("data/agent_discoveries_merged.json").read_text(encoding="utf-8"))}
hits=[]
for u,m in cache.items():
 s=m.get("subscribers") or agent.get(u,0)
 if s<2000: continue
 name=f"{u} {m.get('title') or ''}"
 if not BOOK.search(name): continue
 blob=f"{name} {m.get('description') or ''}"
 if EXAM.search(blob) or "medical book" in (m.get("title") or "").lower() or u.startswith(("med","medical","freemedical","million_medical","neet","mbbs","usmle","plab","mrcp","fmge","pdf4")):
  hits.append((s,u,m.get("title")))
hits.sort(reverse=True)
print(len(hits))
for s,u,t in hits: print(s,u,(t or "")[:50])
