import json,re
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta

BOOK_PAT=re.compile(r"pdf|ebook|\bbooks?\b|bookstore|bookspdf|_books|books_",re.I)
EXAM_PAT=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step\s*[123]|qbank",re.I)

def book_in_name(m):
    s=f"{m.get('username','')} {m.get('title') or ''}"
    if re.search(r"\blibrary\d*\b", s, re.I) and not BOOK_PAT.search(s): return False
    return bool(BOOK_PAT.search(s))

def exam_ok(m):
    blob=" ".join(filter(None,[m.get("username"),m.get("title"),m.get("description")]))
    if EXAM_PAT.search(blob): return True
    t=(m.get("title") or "").lower()
    if "medical book" in t: return True
    u=(m.get("username") or "").lower()
    if u.startswith(("med","medical","medbook","freemedical","million_medical","pdf4yo","neet","mbbs","usmle","plab","mrcp","mccqe","fmge")):
        return True
    return False

def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [("usmle","usmle"),("nbme","usmle"),("kaplan","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]:
        if k in b and t not in out: out.append(t)
    return out or ["mbbs"]

agent={}
for e in json.loads(Path("data/agent_discoveries_merged.json").read_text(encoding="utf-8")):
    agent[e["username"].lower()]=e.get("subscribers_estimate",0)

cache=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8")).get("all",{})
ADD="""medbooksvn2 neetpgmds freemedicalbooks mmedicalbookss medbooksvn booksmedicospdf medical_books_pdf medical_booksy medicalbookspdfs medical_free_ebooks mbs_medicalbooksstore internalmedicinebookss surgery_pdf_books surgeryvideos sketchymedical entvideos pediatric_pdfs pediatrics_books neetpgbooks neet_books neetpdf neetbookspdf mbbsbooks mbbsbookspdf mbbs_books_pdf plabbooks mrcpbooks plabmaterials fmgebooks fmge_books usmle_pdf usmle_books usmlebookspdf plabbookspdf mrcpbookspdf mccqe_books amc_books_pdf neet_pg_pdf medicalboardbooks usmle_kaplan boardsbeyond freesiurgerybooks28 freesurgerybooks pathologybooks cardiobooks pezeshkibooks webofmedical medicalprep medmaterialx tushar_medicalbooks anesthesia_books_pdf critical_care_books ob_gyn_books neurobank_books orthopedic_book gastrointestional_books gastrointestinal_books radiology_ebooks radiologygoldenbooks pharmabookscollection bdsmdsdentalbooks dentist_book ophthbooks ophthalmology_books_2016 uroresources pedsurgery newdermbooks sdgtbookstore medical_book772 medical_books_channel medbooksvn2""".split()

handles=set(cache)|{x.lower() for x in ADD}
meta=dict(cache)
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for u in sorted(handles):
        m=meta.get(u,{})
        subs=m.get("subscribers") or agent.get(u,0)
        if subs>=2000 and book_in_name(m) and exam_ok(m) and m.get("title"): continue
        nm=fetch_channel_meta(c,u)
        if not nm.get("error"): meta[u]=nm

rows=[]
for u,m in meta.items():
    subs=m.get("subscribers") or agent.get(u,0)
    if subs<2000 or not book_in_name(m) or not exam_ok(m): continue
    rows.append({"username":u,"subscribers_estimate":subs,"specialty_tags":tags(m),
        "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{u}","title":m.get("title")})
rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
Path("data/agent_swarm/swarm_exams.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print("COUNT",len(rows))
