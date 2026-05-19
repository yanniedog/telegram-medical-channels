import json,re
from pathlib import Path
import httpx
from discover_channels import HEADERS, fetch_channel_meta, scrape_lyzem_page, TG_HANDLE

MIN=2000
BOOK=re.compile(r"book|pdf|ebook",re.I)
EXAM=re.compile(r"usmle|plab|mrcp|mccqe|amc|neet|mbbs|fmge|inicet|nbme|board|step\s*1|step\s*2|step\s*3|qbank|fmge|pg\s*prep|medical\s+entrance|exam\s+prep|medical\s+student|licensing",re.I)

def book_name(m):
    return bool(BOOK.search(f"{m.get('username','')} {m.get('title') or ''}"))

def exam_ctx(m, agent_tags=None):
    blob=" ".join(filter(None,[m.get('username'),m.get('title'),m.get('description')]))
    if EXAM.search(blob): return True
    if agent_tags and any(t in agent_tags for t in ['usmle','plab','mrcp','mccqe','amc','neet','mbbs','fmge','inicet','board_review','amc_mcq','amc_clinical']):
        return True
    return False

def tags(m):
    b=(f"{m.get('username','')} {m.get('title','')} {m.get('description','')}").lower()
    out=[]
    for k,t in [('usmle','usmle'),('nbme','usmle'),('step 1','usmle'),('step 2','usmle'),('plab','plab'),('mrcp','mrcp'),('mccqe','mccqe'),('amc','amc'),('neet','neet'),('mbbs','mbbs'),('fmge','fmge'),('inicet','inicet'),('board','board_review')]:
        if k in b and t not in out: out.append(t)
    return out or ['exam_prep']

def row(m):
    return {'username':m['username'].lower(),'subscribers_estimate':m.get('subscribers') or 0,
            'specialty_tags':tags(m),'has_direct_ebooks':bool(m.get('has_web_preview')),
            'source_url':m.get('link') or f"https://t.me/{m['username']}",'title':m.get('title')}

agent={}
ap=Path('data/agent_discoveries_merged.json')
if ap.exists():
    for e in json.loads(ap.read_text(encoding='utf-8')):
        agent[e['username'].lower()]=e.get('specialty_tags',[])

cache={}
for p in [Path('data/discovered_channels.json')]:
    if p.exists():
        r=json.loads(p.read_text(encoding='utf-8'))
        cache.update(r.get('all') or {})
        cache.update(r.get('qualified') or {})

# tgstat search scrape
extra=set()
queries=['usmle books pdf','plab books pdf','mrcp books pdf','mccqe books pdf','neet pg books pdf','mbbs books pdf','amc exam books pdf','medical board review pdf']
with httpx.Client(headers=HEADERS,follow_redirects=True,timeout=30) as c:
    for q in queries:
        url=f"https://tgstat.com/channels/search?query={q.replace(' ','+')}"
        try:
            r=c.get(url)
            if r.status_code==200:
                for m in TG_HANDLE.finditer(r.text):
                    h=m.group(1).lower()
                    if h not in ('joinchat','s','share'): extra.add(h)
        except Exception: pass
    for q in ['usmle books pdf channel','plab pdf books','mrcp pdf telegram','neet medical books pdf']:
        for page in range(1,6):
            for h in scrape_lyzem_page(c,q,page): extra.add(h.lower())

handles=set(cache)|extra
# known high-value exam book channels
handles.update('''usmlebooks medical_ebook_pdfs medbooksvn2 neetpgmds freemedicalbooks mmedicalbookss
million_medical_books medicalbooksstoress medicalbooksstorea medicalbooksstore55 medbookspdf pdf4yo
booksmedicospdf medical_books_pdf medical_booksy medicalbookspdfs medical_free_ebooks mbs_medicalbooksstore
surgery_pdf_books surgeryvideos sketchymedical entvideos pediatric_pdfs pediatrics_books patho_videos
cardiology_premium_videos internalmedicinebookss medbooksvn pezeshkibooks dtunewsmedicine medical_books_storess
medicalbookspdf medicalbookspdfs medpdf webofmedical medicalprep nbme_q kaplan_atm store_atm boards_beyonds
usmle_kaplan boardsbeyond usmlestore usmlestep1233 usmlestep_1_2 plab_mrcp mrcp2024 mccqe mccqe_1
neetpgbooks neet_books neetpdf mbbsbooks mbbsbookspdf medusmle medicalusmle_videos amcmcq amcclinical
plabmaterials plabbooks mrcpbooks usmle_pdf usmle_books fmgebooks fmge_books neetbookspdf mbbs_books_pdf
medical_library25 medmaterialx tushar_medicalbooks surgerynb thesurgerytimes internal_medicine_material
medicalusmle usmleworld_pdf usmle_premium_materials plab_pdf_books mrcp_books_pdf mccqe_books amc_books_pdf
neet_pg_pdf fmge_pdf_books medicalboardbooks usmle_step1_books usmle_step2_books plab2books mrcpexamprep
mccqeprep medicalbooksforusmle usmlemedicalbooks plabexambooks mrcpexambooks neetpgmaterials
medical_exam_books medical_exam_pdf exam_books_pdf medexambooks usmlebookspdf plabbookspdf mrcpbookspdf
mbbsmedicalbooks medicalbookhub bscnursing kmtcnursing'''.split())

print('fetching',len(handles))
meta=dict(cache)
with httpx.Client(headers=HEADERS,follow_redirects=True) as c:
    for u in sorted(handles):
        if u in meta and (meta[u].get('subscribers') or 0)>=MIN and meta[u].get('title'):
            pass
        else:
            m=fetch_channel_meta(c,u)
            if not m.get('error'): meta[u]=m

rows=[]
seen=set()
for u,m in meta.items():
    subs=m.get('subscribers') or agent.get(u,{}).get('subscribers_estimate') if isinstance(agent.get(u),dict) else 0
    if isinstance(agent.get(u),list):
        subs=m.get('subscribers') or 0
    ag=agent.get(u,[])
    subs=m.get('subscribers') or 0
    if subs<MIN: continue
    if not book_name(m): continue
    if not exam_ctx(m,ag): continue
    if u in seen: continue
    seen.add(u)
    if not m.get('subscribers'): m['subscribers']=subs
    rows.append(row(m))

rows.sort(key=lambda x:(-x['subscribers_estimate'],x['username']))
out=Path('data/agent_swarm/swarm_exams.json')
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
print('COUNT',len(rows))
for r in rows: print(r['subscribers_estimate'],r['username'])
