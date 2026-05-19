import json,re,time
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta, scrape_lyzem_page, TG_HANDLE

MIN=2000
BOOK_PAT=re.compile(r"pdf|ebook|\bbooks?\b|bookstore|bookspdf|_books|books_|^books",re.I)

def book_in_name(m):
    s=f"{m.get('username','')} {m.get('title') or ''}"
    if re.search(r"\blibrary\d*\b", s, re.I) and not BOOK_PAT.search(s):
        return False
    return bool(BOOK_PAT.search(s))

EXAM_PAT=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board\s*review|boards?\s+beyond|step\s*[123]|qbank|medical\s+entrance|exam\s+prep|medical\s+student|licensing\s+exam",re.I)
EXAM_TAGS={"usmle","plab","mrcp","mccqe","amc","neet","mbbs","fmge","inicet","board_review","amc_mcq","amc_clinical","img","australia"}

def exam_ok(m, ag):
    blob=" ".join(filter(None,[m.get("username"),m.get("title"),m.get("description")]))
    if EXAM_PAT.search(blob): return True
    if ag and EXAM_TAGS.intersection(set(ag)): return True
    t=(m.get("title") or "").lower()
    if "medical book" in t or "medical books" in t: return True
    if (m.get("username") or "").lower() in {"medbookspdf","medicalbooksstoress","medicalbooksstorea","pdf4yo","million_medical_books","freemedicalbooks"}:
        return True
    return False

def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [("usmle","usmle"),("nbme","usmle"),("step 1","usmle"),("step 2","usmle"),("step 3","usmle"),("kaplan","usmle"),("plab","plab"),("mrcp","mrcp"),("mccqe","mccqe"),("amc","amc"),("neet","neet"),("mbbs","mbbs"),("fmge","fmge"),("inicet","inicet"),("board","board_review")]:
        if k in b and t not in out: out.append(t)
    if not out and "medical book" in b: out=["mbbs"]
    return out or ["exam_prep"]

def entry(m, subs):
    return {"username":m["username"].lower(),"subscribers_estimate":subs,"specialty_tags":tags(m),
            "has_direct_ebooks":bool(m.get("has_web_preview")),"source_url":m.get("link") or f"https://t.me/{m['username']}",
            "title":m.get("title")}

agent_subs={}
agent_tags={}
for e in json.loads(Path("data/agent_discoveries_merged.json").read_text(encoding="utf-8")):
    u=e["username"].lower()
    agent_subs[u]=e.get("subscribers_estimate",0)
    agent_tags[u]=e.get("specialty_tags",[])

cache={}
r=json.loads(Path("data/discovered_channels.json").read_text(encoding="utf-8"))
cache.update(r.get("all") or {})

SEEDS="""usmlebooks medical_ebook_pdfs medbooksvn2 medbooksvn neetpgmds neetpgbooks neet_books neetpdf neetbookspdf
medbookspdf medicalbooksstoress medicalbooksstorea medicalbooksstore55 million_medical_books million_medical_book
freemedicalbooks mmedicalbookss pdf4yo booksmedicospdf medical_books_pdf medical_booksy medicalbookspdfs
medical_free_ebooks mbs_medicalbooksstore medical_books_storess pezeshkibooks internalmedicinebookss
surgery_pdf_books surgeryvideos sketchymedical entvideos pediatric_pdfs pediatrics_books pathologybooks
cardiobooks orthopedic_book neurobank_books ob_gyn_books anesthesia_books_pdf critical_care_books
freesurgerybooks28 freesurgerybooks medicalbooksstore55 dtunewsmedicine medicalbookspdf medical_ebook_pdfs
mbbsbooks mbbsbookspdf mbbs_books_pdf mbbsmedicalbooks plabbooks mrcpbooks plabmaterials usmle_pdf usmle_books
fmgebooks fmge_books fmgepdf mccqe_books amc_books_pdf neet_pg_pdf medicalboardbooks usmlebookspdf plabbookspdf
mrcpbookspdf usmle_kaplan boardsbeyond usmlestore usmlestep1233 usmlestep_1_2 medusmle medicalusmle_videos
nbme_q kaplan_atm store_atm boards_beyonds plab_mrcp mrcp2024 mccqe mccqe_1 amcmcq amcclinical amcclinicalexamprep
amcmcqrecalls medical_library25 medmaterialx tushar_medicalbooks surgerynb thesurgerytimes internal_medicine_material
medicalusmle usmleworld_pdf medicalprep medpdf webofmedical medicalbookshare pdfmedbooks medicalbookspdfs
bdsmdsdentalbooks dentist_book pharmabookscollection ophthalmology_books_2016 ophthbooks radiology_ebooks
radiologygoldenbooks gastrointestional_books gastrointestinal_books orthobooksandlectures pedsurgery
uroresources newdermbooks sdgtbookstore bscnursing kmtcnursing medical_book772 medical_books_channel
medicalbooksforusmle usmlemedicalbooks plabexambooks mrcpexambooks medical_exam_books medical_exam_pdf
exam_books_pdf medexambooks usmle_premium_materials plab_pdf_books mrcp_books_pdf usmle_step1_books usmle_step2_books
plab2books mrcpexamprep mccqeprep neetpgmaterials medicalbookhub cardiology_premium_videos patho_videos surgerynb""".split()

handles=set(cache)|{s.lower() for s in SEEDS}
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for q in ["usmle books pdf telegram","plab books pdf","mrcp books pdf","mccqe books pdf","neet pg books pdf","mbbs books pdf telegram","amc exam books pdf","fmge books pdf","medical board review books pdf","usmle step 1 pdf books","kaplan usmle books pdf","medical exam books pdf channel"]:
        for page in range(1,8):
            for h in scrape_lyzem_page(c,q,page): handles.add(h.lower())
            time.sleep(0.25)
    try:
        for q in ["usmle+books+pdf","plab+books+pdf","mrcp+books+pdf","neet+pg+books+pdf","mbbs+books+pdf"]:
            r=c.get(f"https://tgstat.com/channels/search?query={q}")
            if r.status_code==200:
                for m in TG_HANDLE.finditer(r.text):
                    h=m.group(1).lower()
                    if h not in ("joinchat","s","share"): handles.add(h)
    except Exception: pass

meta=dict(cache)
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for i,u in enumerate(sorted(handles)):
        m=meta.get(u,{})
        subs=m.get("subscribers") or agent_subs.get(u,0)
        if subs>=MIN and m.get("title") and book_in_name(m) and exam_ok(m, agent_tags.get(u,[])):
            continue
        nm=fetch_channel_meta(c,u)
        if not nm.get("error"): meta[u]=nm
        time.sleep(0.2)

rows=[]
seen=set()
for u,m in meta.items():
    subs=m.get("subscribers") or agent_subs.get(u,0)
    if subs<MIN: continue
    if not book_in_name(m): continue
    if not exam_ok(m, agent_tags.get(u,[])): continue
    if u in seen: continue
    seen.add(u)
    rows.append(entry(m, subs))

rows.sort(key=lambda x:(-x["subscribers_estimate"], x["username"]))
out=Path("data/agent_swarm/swarm_exams.json")
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
print("COUNT",len(rows))
for r in rows: print(r["subscribers_estimate"], r["username"], (r.get("title") or "")[:45])
