import json, re
from pathlib import Path
from health_relevance import health_relevance_score, HEALTH_RE

data = json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))
all_ch = data.get("all", data)
USERNAME = re.compile(r"books?|pdfs?|ebooks?", re.I)
MED = re.compile(r"med(?:ical|icine|ico)?|medic|pharm|surg|dent|nurs|clinic|hospital|usmle|mbbs|mrcp|plab|pathol|radiol|cardio|neuro|psych|ophthal|gyn|obgyn|pediat|ortho|urolog|derma|anesth|emerg|doctor|physician|mccqe|amc|nbme|pezeshki|medicina|medico", re.I)
rows = []
for k,v in all_ch.items():
    u = v.get("username","")
    if not USERNAME.search(u): continue
    subs = v.get("subscribers") or 0
    if subs < 2000: continue
    generic = not MED.search(u)
    title = v.get("title") or ""
    desc = v.get("description") or ""
    score, reasons = health_relevance_score(u, title, desc)
    rows.append((generic, u, subs, score, title[:50]))
rows.sort(key=lambda x:(not x[0], -x[3], -x[2]))
print("total", len(rows), "generic", sum(1 for r in rows if r[0]))
for r in rows[:50]:
    print(r)
