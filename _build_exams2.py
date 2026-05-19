import json,re,time
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta, scrape_lyzem_page

MIN_SUBS=2000
OUT=Path("data/agent_swarm/swarm_exams.json")
BOOK=re.compile(r"book|pdf|ebook",re.I)
EXAM=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step\s*1|step\s*2|step\s*3|qbank|fmge|pg\s*prep|medical\s+entrance|exam\s+prep",re.I)

QUERIES=[
 "usmle books pdf","usmle pdf books channel","usmle step 1 books pdf",
 "usmle step 2 ck books","usmle qbank pdf","kaplan usmle books pdf",
 "plab books pdf","plab 1 books pdf","plab 2 books pdf","plab pdf channel",
 "mrcp books pdf","mrcp part 1 pdf books","mrcp part 2 books pdf",
 "mccqe books pdf","mccqe part 1 pdf","canada mccqe books",
 "amc mcq books pdf","amc exam books pdf","australian medical exam books pdf",
 "neet pg books pdf","neet pg pdf books","neet ss books pdf","neet medical books",
 "mbbs books pdf","mbbs 1st year books pdf","mbbs pdf books telegram",
 "fmge books pdf","fmge pdf channel","medical board review books pdf",
 "medical exam books pdf","entrance exam medical books pdf",
 "plab mrcp books pdf","usmle plab books","medical licensing exam books pdf",
]

# large seed list from tgstat/lyzem/common handles
SEEDS="""
usmlebooks usmlestore usmlestep1233 usmlestep_1_2 medusmle medicalusmle_videos
nbme_q boards_beyonds kaplan_atm store_atm mccqe mccqe_1 plab_mrcp mrcp2024
plabmaterials plabbooks mrcpbooks mrcp_pdf usmle_pdf usmle_books usmlestep1books
neetpgbooks neet_books neetpdf neetpgmds mbbsbooks mbbs_books_pdf mbbsbookspdf
medbookspdf medical_ebook_pdfs medbooksvn medbooksvn2 million_medical_books
medicalbooksstoress medicalbooksstorea pdf4yo medpdf medicalprep freemedicalbooks
medical_free_ebooks medicalbookspdfs pdfmedbooks medical_library25 medmaterialx
mmedicalbookss booksmedicospdf medical_books_pdf medical_booksy tushar_medicalbooks
usmleworld_pdf usmle_world_books plab_pdf_books mrcp_books_pdf mccqe_books
amc_books_pdf neet_pg_pdf fmge_pdf_books board_review_pdf medicalboardbooks
usmle_step1_books usmle_step2_books plab2books mrcpexamprep mccqeprep
medicalusmle usmle_materials usmle_premium_materials plab_materials
fmgebooks fmge_books fmgepdf neetpgmaterials neetpgbookschannel
mbbsmedicalbooks mbbs_medical_books medicalbooksforusmle usmlemedicalbooks
plabexambooks mrcpexambooks mccqemedicalbooks amcexambooks amcbooks
medicalbooksforneet neetbookspdf mbbsbookstore medicalbookhub
usmlebookspdf plabbookspdf mrcpbookspdf neetbookspdf mbbsbookspdf
medical_exam_books medical_exam_pdf exam_books_pdf medexambooks
""".split()

def book_name(meta):
    return bool(BOOK.search(f"{meta.get('username','')} {meta.get('title','') or ''}"))

def exam_ctx(meta):
    blob=" ".join(filter(None,[meta.get('username'),meta.get('title'),meta.get('description')]))
    return bool(EXAM.search(blob))

def tags(meta):
    b=(f"{meta.get('username','')} {meta.get('title','')} {meta.get('description','')}").lower()
    m=[("usmle","usmle"),("nbme","usmle"),("step 1","usmle"),("step 2","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]
    out=[]
    for k,t in m:
        if k in b and t not in out: out.append(t)
    return out or ["exam_prep"]

def row(meta):
    return {"username":meta["username"].lower(),"subscribers_estimate":meta.get("subscribers") or 0,
            "specialty_tags":tags(meta),"has_direct_ebooks":bool(meta.get("has_web_preview")),
            "source_url":meta.get("link") or f"https://t.me/{meta['username']}","title":meta.get("title")}

cache={}
p=Path("data/discovered_channels.json")
if p.exists():
    r=json.loads(p.read_text(encoding="utf-8"))
    cache.update(r.get("all") or {})
    cache.update(r.get("qualified") or {})
seen=set(cache)|{s.lower() for s in SEEDS}
meta=dict(cache)
with httpx.Client(headers=HEADERS,follow_redirects=True) as client:
    for q in QUERIES:
        for page in range(1,12):
            b=scrape_lyzem_page(client,q,page)
            if not b and page>1: break
            for h in b: seen.add(h.lower())
            time.sleep(0.28)
        time.sleep(0.35)
    print("handles",len(seen))
    for i,u in enumerate(sorted(seen)):
        m=meta.get(u,{})
        if (m.get("subscribers") or 0)>=MIN_SUBS and m.get("title") and book_name(m) and exam_ctx(m):
            continue
        nm=fetch_channel_meta(client,u)
        if nm.get("error"): continue
        meta[u]=nm
        if (i+1)%40==0:
            n=sum(1 for x in meta.values() if (x.get("subscribers") or 0)>=MIN_SUBS and book_name(x) and exam_ctx(x))
            print(i+1,n)
        time.sleep(0.22)

rows=[row(m) for m in meta.values() if (m.get("subscribers") or 0)>=MIN_SUBS and book_name(m) and exam_ctx(m)]
rows.sort(key=lambda x:(-x["subscribers_estimate"],x["username"]))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print("COUNT",len(rows))
for r in rows: print(r["subscribers_estimate"],r["username"])
