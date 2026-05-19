import json,re,time
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta, scrape_lyzem_page

MIN_SUBS=2000
OUT=Path("data/agent_swarm/swarm_exams.json")
EXAMS=["usmle","plab","mrcp","mccqe","amc","neet","mbbs","fmge","inicet","nbme","board","step1","step2","step3","qbank","fmge","pgprep"]
EXAM_RE=re.compile("|".join(re.escape(x) for x in EXAMS),re.I)
BOOK_RE=re.compile(r"book|pdf|ebook",re.I)

QUERIES=[
 "USMLE books pdf","USMLE step 1 pdf channel","USMLE step 2 pdf books",
 "PLAB books pdf telegram","PLAB 1 pdf channel","PLAB 2 books",
 "MRCP books pdf","MRCP part 1 pdf","MRCP part 2 books telegram",
 "MCCQE books pdf","MCCQE part 1 pdf channel",
 "AMC MCQ books pdf","AMC exam pdf telegram",
 "NEET PG books pdf","NEET PG pdf channel","NEET SS books",
 "MBBS books pdf telegram","MBBS 1st year books pdf",
 "FMGE books pdf","medical board review pdf",
 "USMLE qbank pdf","Kaplan USMLE pdf books",
 "medical exam books pdf telegram","PLAB MRCP USMLE books",
 "medical entrance books pdf","ini cet books pdf",
]

SEEDS=[
 "usmlebooks","usmlestore","usmlestep1233","usmlestep_1_2","medusmle","medicalusmle_videos",
 "nbme_q","mccqe","mccqe_1","plab_mrcp","mrcp2024","plabmaterials","plabbooks","mrcpbooks",
 "mrcp_pdf","usmle_pdf","usmle_books","usmlestep1books","neetpgbooks","neet_books","neetpdf",
 "mbbsbooks","mbbs_books_pdf","mbbsbookspdf","medbookspdf","medical_ebook_pdfs","medbooksvn2",
 "million_medical_books","medicalbooksstoress","medicalbooksstorea","pdf4yo","medpdf","medicalprep",
 "freemedicalbooks","medical_free_ebooks","medicalbookspdfs","pdfmedbooks","medical_library25",
 "medmaterialx","mmedicalbookss","booksmedicospdf","medical_books_pdf","medical_booksy",
 "usmleworld_pdf","usmle_world_books","plab_pdf_books","mrcp_books_pdf","mccqe_books",
 "amc_books_pdf","neet_pg_pdf","fmge_pdf_books","board_review_pdf","medicalboardbooks",
 "usmle_step1_books","usmle_step2_books","plab2books","mrcpexamprep","mccqeprep",
]

def book_in_name(meta):
    s=f"{meta.get('username','')} {meta.get('title','')}"
    return bool(BOOK_RE.search(s))

def exam_hit(meta):
    s=" ".join(filter(None,[meta.get('username'),meta.get('title'),meta.get('description')]))
    return bool(EXAM_RE.search(s))

def tags_for(meta):
    blob=(f"{meta.get('username','')} {meta.get('title','')} {meta.get('description','')}").lower()
    out=[]
    mapping=[("usmle","usmle"),("nbme","usmle"),("step 1","usmle"),("step 2","usmle"),("step 3","usmle"),
             ("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),
             ("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]
    for k,t in mapping:
        if k in blob and t not in out: out.append(t)
    return out or ["exam_prep"]

def entry(meta):
    return {"username":meta["username"].lower(),"subscribers_estimate":meta.get("subscribers") or 0,
            "specialty_tags":tags_for(meta),"has_direct_ebooks":bool(meta.get("has_web_preview")),
            "source_url":meta.get("link") or f"https://t.me/{meta['username']}","title":meta.get("title")}

cached={}
p=Path("data/discovered_channels.json")
if p.exists():
    raw=json.loads(p.read_text(encoding="utf-8"))
    cached.update(raw.get("all") or {})
    cached.update(raw.get("qualified") or {})
seen=set(cached)|{s.lower() for s in SEEDS}
meta_map=dict(cached)
with httpx.Client(headers=HEADERS,follow_redirects=True) as client:
    for q in QUERIES:
        for page in range(1,10):
            hs=scrape_lyzem_page(client,q,page)
            if not hs and page>1: break
            for h in hs: seen.add(h.lower())
            time.sleep(0.3)
        time.sleep(0.4)
    print("handles",len(seen))
    for i,u in enumerate(sorted(seen)):
        m=meta_map.get(u,{})
        if (m.get("subscribers") or 0)>=MIN_SUBS and m.get("title") and book_in_name(m) and exam_hit(m):
            continue
        nm=fetch_channel_meta(client,u)
        if nm.get("error"): continue
        meta_map[u]=nm
        if (i+1)%30==0:
            c=sum(1 for x in meta_map.values() if (x.get("subscribers") or 0)>=MIN_SUBS and book_in_name(x) and exam_hit(x))
            print(i+1,"matched",c)
        time.sleep(0.25)

rows=[entry(m) for m in meta_map.values() if (m.get("subscribers") or 0)>=MIN_SUBS and book_in_name(m) and exam_hit(m)]
rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE",OUT,"COUNT",len(rows))
for r in rows[:40]:
    print(r["subscribers_estimate"],r["username"],r.get("title","")[:50])
