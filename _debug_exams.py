import json,re
from pathlib import Path
BOOK=re.compile(r"\b(book|pdf|ebook|e-?book)\b",re.I)
raw=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))
allm=raw.get("all") or {}
for u,m in sorted(allm.items(), key=lambda x:-(x[1].get("subscribers") or 0)):
 subs=m.get("subscribers") or 0
 if subs<2000: continue
 name=f"{m.get('username','')} {m.get('title','')}"
 if BOOK.search(name):
  print(subs,u,(m.get('title') or '')[:70])
