"""Analyze scraped posts: formats, languages, specialties, years, scores."""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from langdetect import detect, detect_langs, LangDetectException
except ImportError:
    detect = None

# --- Specialty keyword maps ---
SPECIALTY_RULES: list[tuple[str, re.Pattern]] = [
    ("Anatomy", re.compile(r"\banatomy\b|\batlas of human\b|\bnetter\b|\bgray'?s anatomy\b", re.I)),
    ("Physiology", re.compile(r"\bphysiology\b|\bguyton\b|\bganong\b", re.I)),
    ("Biochemistry", re.compile(r"\bbiochemistry\b|\bharper\b|\blippincott biochem", re.I)),
    ("Pathology", re.compile(r"\bpathology\b|\brobbins\b|\bcotran\b|\bhistopath", re.I)),
    ("Pharmacology", re.compile(r"\bpharmacology\b|\bkatzung\b|\blippincott pharma\b|\bnursing.*drug handbook\b", re.I)),
    ("Microbiology", re.compile(r"\bmicrobiology\b|\bimmunology\b|\bsketchy micro\b", re.I)),
    ("Internal Medicine", re.compile(r"\binternal medicine\b|\bharrison\b|\bcecil\b|\bCMDT\b|\bOxford handbook clinical medicine\b", re.I)),
    ("Surgery", re.compile(r"\bsurgery\b|\bsurgical\b|\bbailey\b.*love\b|\bsabiston\b|\bschwartz\b", re.I)),
    ("Obstetrics & Gynaecology", re.compile(r"\bobstetric|\bgynaec|\bgynec|\bDC Dutta\b|\bwilliams obstetric", re.I)),
    ("Paediatrics", re.compile(r"\bpaediatric|\bpediatric|\bnelson\b.*pediatric|\bnelson textbook\b", re.I)),
    ("Psychiatry", re.compile(r"\bpsychiatr|\bDSM\b|\bstahl\b", re.I)),
    ("Radiology", re.compile(r"\bradiolog|\bimaging\b|\bFRCR\b|\bMRI\b|\bCT scan\b", re.I)),
    ("Emergency Medicine", re.compile(r"\bemergency medicine\b|\bATLS\b|\btintinalli\b", re.I)),
    ("Cardiology", re.compile(r"\bcardiol|\bheart failure\b|\bechocardio", re.I)),
    ("Neurology", re.compile(r"\bneurol|\bneurosurg", re.I)),
    ("Dermatology", re.compile(r"\bdermatol", re.I)),
    ("Anaesthesia", re.compile(r"\banaesth|\banesthes", re.I)),
    ("Nursing", re.compile(r"\bnursing\b", re.I)),
    ("USMLE / Board exams", re.compile(r"\bUSMLE\b|\bStep [123]\b|\bFirst Aid\b|\bNBME\b|\bUWorld\b", re.I)),
    ("AMC / Australian exams", re.compile(r"\bAMC\b|\bMCCQE\b|\bRACGP\b|\bFRACGP\b|\bFRACP\b|\bRANZCR\b|\bAustralian medical council\b", re.I)),
    ("General Practice", re.compile(r"\bgeneral practice\b|\bfamily medicine\b|\bprimary care\b", re.I)),
    ("Public Health / Epidemiology", re.compile(r"\bpublic health\b|\bepidemiol|\bbiostatistic", re.I)),
    ("Dental", re.compile(r"\bdental\b|\bodonto|\b dentistry\b", re.I)),
    ("Ophthalmology", re.compile(r"\bophthalmol|\bophthalmic|\bretina\b|\bglaucoma\b|\bcataract\b", re.I)),
    ("ENT / Otolaryngology", re.compile(r"\botolaryngol|\bENT\b|\bear nose throat", re.I)),
    ("Pharmacy", re.compile(r"\bpharmacy\b|\bpharmacist\b|\bBNF\b|\bformulary\b", re.I)),
    ("Physiotherapy", re.compile(r"\bphysiotherap|\bfisioterap|\bkinesiolog", re.I)),
    ("Dermatology", re.compile(r"\bdermatol|\bskin\b.*\bbook", re.I)),
    ("Wilderness / Rural", re.compile(r"\bwilderness\b|\brural medicine\b|\bremote medicine\b|\btropical medicine\b", re.I)),
    ("Medicolegal", re.compile(r"\bmedicolegal\b|\bmalpractice\b|\bforensic medicine\b", re.I)),
    ("Australian MBS/PBS", re.compile(r"\bMBS\b|\bPBS\b|\bMedicare\b|\bbenefits schedule\b|\bpharmaceutical benefits\b", re.I)),
    ("Business for Doctors", re.compile(r"\bbusiness for doctors\b|\bpractice management\b|\bmedical billing\b", re.I)),
    ("Urology", re.compile(r"\burology\b|\burological\b", re.I)),
    ("Orthopedics", re.compile(r"\borthopedic|\borthopaedic|\btrauma\b.*\bfracture", re.I)),
    ("Neurosurgery", re.compile(r"\bneurosurg|\bneurosurgical\b", re.I)),
    ("Gastroenterology", re.compile(r"\bgastroenterol|\bhepatolog|\bGI\b.*\bbook", re.I)),
    ("Nephrology", re.compile(r"\bnephrol|\bdialysis\b|\brenal\b", re.I)),
    ("Endocrinology", re.compile(r"\bendocrin|\bdiabetes\b|\bthyroid\b", re.I)),
    ("Hematology / Oncology", re.compile(r"\bhematol|\boncolog|\bcancer\b.*\bbook", re.I)),
    ("Pulmonology", re.compile(r"\bpulmonol|\brespiratory\b|\bchest medicine\b", re.I)),
    ("Infectious Disease", re.compile(r"\binfectious disease\b|\bIDSA\b|\bantimicrobial\b", re.I)),
    ("Geriatrics", re.compile(r"\bgeriatric|\belderly\b.*\bmedicine", re.I)),
    ("Critical Care / ICU", re.compile(r"\bcritical care\b|\bintensive care\b|\bICU\b", re.I)),
    ("Pain Medicine", re.compile(r"\bpain medicine\b|\banalgesia\b", re.I)),
    ("Plastic Surgery", re.compile(r"\bplastic surgery\b|\breconstructive\b", re.I)),
    ("Vascular Surgery", re.compile(r"\bvascular surgery\b|\bendovascular\b", re.I)),
    ("Medical Laboratory", re.compile(r"\blaboratory medicine\b|\bclinical chemistry\b|\bMLT\b", re.I)),
    ("PLAB / MRCP", re.compile(r"\bPLAB\b|\bMRCP\b|\bMRCS\b", re.I)),
    ("Other clinical", re.compile(r"\bclinical\b|\bmedicine\b|\bmedical\b", re.I)),
]

PUBLISHER_REGION_RULES: list[tuple[str, re.Pattern]] = [
    ("United States", re.compile(r"\bElsevier\b|\bSaunders\b|\bLippincott\b|\bWolters Kluwer\b|\bMcGraw\b|\bUSMLE\b|\bAmerican\b", re.I)),
    ("United Kingdom", re.compile(r"\bOxford University Press\b|\bCambridge\b|\bBMJ\b|\bBritish\b|\bBNF\b|\bBritish Pharmacopoeia\b|\bHodder Arnold\b", re.I)),
    ("Australia / NZ", re.compile(r"\bAustralian\b|\bRACGP\b|\bAMC\b|\bTherapeutic Guidelines\b|\beTG\b|\bMJA\b|\bANZ\b|\bNew Zealand\b", re.I)),
    ("Europe (other)", re.compile(r"\bSpringer\b|\bThieme\b|\bGeorg Thieme\b|\bGerman\b|\bFrench\b", re.I)),
    ("India / South Asia", re.compile(r"\bIndian\b|\bJaypee\b|\bPrepLadder\b|\bNEET\b|\bINICET\b|\bAIIMS\b", re.I)),
    ("Middle East / Arabic", re.compile(r"\bArabic\b|\bSaudi\b|\bUAE\b|\bمليون\b", re.I)),
    ("International / unknown", re.compile(r".", re.I)),
]

YEAR_RE = re.compile(r"\b(19[89]\d|20[0-3]\d)\b")
EDITION_YEAR_RE = re.compile(
    r"(?:edition|ed\.?|vol\.?|volume)\s*[,\s]*(\d{4})|(\d{1,2})(?:st|nd|rd|th)\s+edition\s*\(?(\d{4})?\)?",
    re.I,
)

EBOOK_EXT = {"pdf", "epub", "djvu", "mobi", "azw3", "fb2", "cbr", "cbz"}
OTHER_BOOK_EXT = {"chm", "rar", "zip", "7z"}
PPT_EXT = {"ppt", "pptx"}
APK_EXT = {"apk"}
AV_EXT = {"mp4", "mkv", "avi", "mov", "mp3", "m4a", "wav", "video", "audio"}


def safe_lang(text: str) -> str | None:
    if not text or len(text.strip()) < 20:
        return None
    if not detect:
        return None
    try:
        return detect(text)
    except LangDetectException:
        return None


def top_langs(texts: list[str], n: int = 3) -> list[tuple[str, int]]:
    c: Counter[str] = Counter()
    for t in texts:
        lang = safe_lang(t)
        if lang:
            c[lang] += 1
    return c.most_common(n)


def normalize_title(text: str, file_names: list[str]) -> str:
    src = " ".join(file_names) if file_names else text
    src = re.sub(r"\.(pdf|epub|djvu|mobi)\b", "", src, flags=re.I)
    src = re.sub(r"\s+", " ", src).strip().lower()
    src = re.sub(r"\b\d+(?:st|nd|rd|th)?\s+edition\b", " edition", src, flags=re.I)
    src = re.sub(r"\bedition\s*\d+\b", " edition", src, flags=re.I)
    src = re.sub(r"\b(19|20)\d{2}\b", "", src)
    src = re.sub(r"[^\w\s]", " ", src)
    src = re.sub(r"\s+", " ", src).strip()
    return src[:200] if src else ""


def extract_year(text: str) -> int | None:
    years = [int(y) for y in YEAR_RE.findall(text) if 1985 <= int(y) <= 2030]
    if not years:
        return None
    # prefer likely publication years (not view counts etc.)
    plausible = [y for y in years if y <= datetime.now().year + 1]
    return max(plausible) if plausible else None


def classify_specialties(text: str) -> list[str]:
    found = []
    for name, pat in SPECIALTY_RULES:
        if pat.search(text) and name not in found:
            found.append(name)
    return found or ["Unclassified"]


def classify_region(text: str) -> str:
    for region, pat in PUBLISHER_REGION_RULES[:-1]:
        if pat.search(text):
            return region
    return "International / unknown"


# External storefront / catalog pages (subscription sites, not Telegram-hosted files)
EXTERNAL_BOOK_STORE_RE = re.compile(
    r"ophthbooks\.com|/More\.aspx\?|/product/|/subscribe|membership|"
    r"paywall|checkout|cart\.|bookshop\.|\.store/|medbooks\.store|"
    r"webofmedical\.com/(?!.*\.(pdf|epub))|buy now|purchase|premium access",
    re.I,
)

BOOK_CATALOG_TEXT_RE = re.compile(
    r"\\|/|textbook|atlas|handbook|manual|edition|vol\.?\s*\d|"
    r"\b(pdf|epub|ebook|book)\b",
    re.I,
)


def has_direct_hosted_ebook(post: dict) -> bool:
    """True only when the channel posts an actual file attachment on Telegram."""
    if not post.get("has_direct_file"):
        return False
    exts = set(post.get("file_extensions") or [])
    if exts & EBOOK_EXT:
        return True
    if exts & OTHER_BOOK_EXT:
        return True
    for fn in post.get("file_names") or []:
        if re.search(r"\.(pdf|epub|djvu|mobi|azw3|cbz|cbr)\b", fn, re.I):
            return True
    text = (post.get("text") or "") + " " + " ".join(post.get("file_names") or [])
    if re.search(r"\b\.(pdf|epub|djvu|mobi)\b", text, re.I):
        return True
    return False


def is_ebook_post(post: dict) -> bool:
    """Loose book-related post (includes external links). Prefer has_direct_hosted_ebook for inclusion."""
    if has_direct_hosted_ebook(post):
        return True
    exts = set(post.get("file_extensions") or [])
    text = (post.get("text") or "") + " " + " ".join(post.get("file_names") or [])
    if re.search(r"\b\.(pdf|epub|djvu|mobi)\b", text, re.I):
        return True
    text_l = text.lower()
    if re.search(
        r"download.*\.(pdf|epub)|free download|google drive|gdrive|pdf free|ebook",
        text_l,
    ):
        return True
    if re.search(
        r"\b(harrison|robbins|gray.?s anatomy|netter|sabiston|bailey.*love|"
        r"first aid|pathologic basis|lippincott|elsevier)\b.*\b(edition|pdf)\b",
        text_l,
    ):
        return True
    if re.search(r"\b(download|get).{0,40}\b(book|textbook|atlas|manual|handbook|guide)\b", text_l):
        return True
    if re.search(r"\b(book|textbook|atlas|manual|handbook).{0,40}\b(free|download|pdf|epub)\b", text_l):
        return True
    if post.get("file_names") and len((post.get("text") or "")) > 30:
        return True
    return False


def is_direct_ebook_post(post: dict) -> bool:
    """Ebook that is hosted as a file on Telegram (required for channel inclusion)."""
    return has_direct_hosted_ebook(post)


def is_link_only_channel_post(post: dict) -> bool:
    """Promotes books elsewhere: external sites, other channels, no Telegram file."""
    if post.get("is_link_only_channel_promo"):
        return True
    if has_direct_hosted_ebook(post):
        return False
    text = post.get("text") or ""
    urls = post.get("external_urls") or []
    if urls:
        for u in urls:
            if EXTERNAL_BOOK_STORE_RE.search(u):
                return True
        if BOOK_CATALOG_TEXT_RE.search(text) or is_ebook_post(post):
            return True
    if re.search(r"join\s+@|backup channel|subscribe to @|our channel @", text, re.I):
        return True
    if re.fullmatch(r"(@\w+\s*)+", text.strip()):
        return True
    if not post.get("has_direct_file") and bool(
        re.findall(r"t\.me/\+?[A-Za-z0-9_]+", text)
    ):
        return True
    return False


def channel_requires_direct_files(posts: list[dict], min_direct: int = 1) -> tuple[bool, str]:
    """Channel-level gate: must host ebook files on Telegram, not only external catalogs."""
    if not posts:
        return False, "no_posts_scraped"
    direct = sum(1 for p in posts if is_direct_ebook_post(p))
    if direct < min_direct:
        external_bookish = sum(
            1
            for p in posts
            if is_link_only_channel_post(p) and (p.get("external_urls") or is_ebook_post(p))
        )
        if external_bookish >= max(3, len(posts) // 10):
            return False, "external_catalog_only_no_telegram_files"
        return False, "no_direct_telegram_ebooks"
    link_ratio = sum(1 for p in posts if is_link_only_channel_post(p)) / len(posts)
    if link_ratio > 0.85 and direct < 3:
        return False, "mostly_external_links"
    return True, "ok"


@dataclass
class ChannelAnalysis:
    username: str
    subscribers: int | None
    scrape_source: str
    posts_total: int
    posts_scraped: int
    ebook_posts: int
    link_only_posts: int
    pdf_count: int
    epub_count: int
    other_book_count: int
    ppt_count: int
    apk_count: int
    av_count: int
    channel_langs_top3: str
    book_langs_top3: str
    specialty_json: str
    region_json: str
    year_histogram_json: str
    first_post_date: str | None
    last_ebook_date: str | None
    channel_created_proxy: str | None
    posts_per_day: float | None
    ebooks_per_day: float | None
    total_views_ebooks: int
    post_to_ebook_view_ratio: float | None
    uniqueness_score: float | None
    breadth_score: float | None
    unique_titles: int
    data_coverage_pct: float
    top_keywords_json: str = "[]"
    top_bigrams_json: str = "[]"
    specialty_keyword_hits_json: str = "{}"
    top_keyword_1: str | None = None
    top_keyword_1_count: int = 0
    top_keyword_2: str | None = None
    top_keyword_2_count: int = 0
    top_keyword_3: str | None = None
    top_keyword_3_count: int = 0
    unique_tokens: int = 0
    total_tokens: int = 0
    agent_specialty_tags_json: str = "[]"
    notes: str = ""


def analyze_channel(
    username: str,
    posts: list[dict],
    subscribers: int | None,
    source: str,
    channel_meta: dict | None = None,
) -> ChannelAnalysis:
    ebook_posts_list = [p for p in posts if is_direct_ebook_post(p)]
    link_only = sum(1 for p in posts if is_link_only_channel_post(p))

    pdf_c = epub_c = other_b = ppt_c = apk_c = av_c = 0
    channel_texts = []
    book_texts = []
    specialties: Counter[str] = Counter()
    regions: Counter[str] = Counter()
    years: Counter[int] = Counter()
    titles: list[str] = []
    views_ebooks = 0

    for p in posts:
        channel_texts.append(p.get("text") or "")
    for p in ebook_posts_list:
        text = (p.get("text") or "") + " " + " ".join(p.get("file_names") or [])
        book_texts.append(text)
        exts = set(p.get("file_extensions") or [])
        if "pdf" in exts or re.search(r"\.pdf", text, re.I):
            pdf_c += 1
        if "epub" in exts or re.search(r"\.epub", text, re.I):
            epub_c += 1
        if exts & OTHER_BOOK_EXT:
            other_b += 1
        if exts & PPT_EXT or re.search(r"\.pptx?", text, re.I):
            ppt_c += 1
        if exts & APK_EXT:
            apk_c += 1
        if exts & AV_EXT:
            av_c += 1
        for sp in classify_specialties(text):
            specialties[sp] += 1
        regions[classify_region(text)] += 1
        y = extract_year(text)
        if y:
            years[y] += 1
        nt = normalize_title(p.get("text") or "", p.get("file_names") or [])
        if len(nt) > 8:
            titles.append(nt)
        if p.get("views"):
            views_ebooks += int(p["views"])

    ch_langs = top_langs(channel_texts)
    bk_langs = top_langs(book_texts)

    dates = []
    ebook_dates = []
    for p in posts:
        if p.get("datetime_utc"):
            try:
                dates.append(datetime.fromisoformat(p["datetime_utc"].replace("Z", "+00:00")))
            except ValueError:
                pass
    for p in ebook_posts_list:
        if p.get("datetime_utc"):
            try:
                ebook_dates.append(datetime.fromisoformat(p["datetime_utc"].replace("Z", "+00:00")))
            except ValueError:
                pass

    first_post = min(dates).date().isoformat() if dates else None
    last_ebook = max(ebook_dates).date().isoformat() if ebook_dates else None
    created_proxy = first_post

    posts_per_day = None
    ebooks_per_day = None
    if dates and len(dates) >= 2:
        span = (max(dates) - min(dates)).days or 1
        posts_per_day = round(len(posts) / span, 3)
        if ebook_dates:
            ebooks_per_day = round(len(ebook_posts_list) / span, 3)

    total_views_all = sum(p.get("views") or 0 for p in posts)
    ratio = None
    if views_ebooks and len(posts):
        ratio = round(len(posts) / (views_ebooks / max(len(ebook_posts_list), 1)), 6)

    unique_titles = len(set(titles))

    from keyword_analyzer import extract_keywords

    kw = extract_keywords(posts, channel_meta)
    agent_tags = []
    if channel_meta:
        agent_tags = channel_meta.get("agent_specialty_tags") or []

    return ChannelAnalysis(
        username=username,
        subscribers=subscribers,
        scrape_source=source,
        posts_total=len(posts),
        posts_scraped=len(posts),
        ebook_posts=len(ebook_posts_list),
        link_only_posts=link_only,
        pdf_count=pdf_c,
        epub_count=epub_c,
        other_book_count=other_b,
        ppt_count=ppt_c,
        apk_count=apk_c,
        av_count=av_c,
        channel_langs_top3=json.dumps(ch_langs),
        book_langs_top3=json.dumps(bk_langs),
        specialty_json=json.dumps(dict(specialties.most_common())),
        region_json=json.dumps(dict(regions.most_common())),
        year_histogram_json=json.dumps(dict(sorted(years.items()))),
        first_post_date=first_post,
        last_ebook_date=last_ebook,
        channel_created_proxy=created_proxy,
        posts_per_day=posts_per_day,
        ebooks_per_day=ebooks_per_day,
        total_views_ebooks=views_ebooks,
        post_to_ebook_view_ratio=ratio,
        uniqueness_score=None,
        breadth_score=None,
        unique_titles=unique_titles,
        data_coverage_pct=_coverage_pct(posts, source),
        top_keywords_json=kw["top_keywords_json"],
        top_bigrams_json=kw["top_bigrams_json"],
        specialty_keyword_hits_json=kw["specialty_keyword_hits_json"],
        top_keyword_1=kw["top_keyword_1"],
        top_keyword_1_count=kw["top_keyword_1_count"],
        top_keyword_2=kw["top_keyword_2"],
        top_keyword_2_count=kw["top_keyword_2_count"],
        top_keyword_3=kw["top_keyword_3"],
        top_keyword_3_count=kw["top_keyword_3_count"],
        unique_tokens=kw["unique_tokens"],
        total_tokens=kw["total_tokens"],
        agent_specialty_tags_json=json.dumps(agent_tags),
        notes="",
    )


def _coverage_pct(posts: list[dict], source: str) -> float:
    if not posts:
        return 0.0
    max_id = max(p.get("post_id") or 0 for p in posts)
    scraped = len(posts)
    if source == "tgstat_sample":
        return round(min(25.0, scraped * 1.2), 1)
    if source == "tme_partial_preview":
        return round(min(60.0, scraped / max(max_id, 1) * 100 * 2), 1)
    # full preview pagination
    if max_id > 0:
        return round(min(100.0, (scraped / max_id) * 100 * 1.15), 1)
    return 90.0 if scraped > 200 else 50.0


def compute_cross_channel_scores(analyses: list[ChannelAnalysis], all_titles: dict[str, set[str]]) -> None:
    all_book_titles: Counter[str] = Counter()
    for titles in all_titles.values():
        for t in titles:
            all_book_titles[t] += 1

    for a in analyses:
        titles = all_titles.get(a.username.lower(), set())
        if not titles:
            a.uniqueness_score = 0.0
            a.breadth_score = 0.0
            continue
        unique = sum(1 for t in titles if all_book_titles[t] == 1)
        a.uniqueness_score = round(100.0 * unique / len(titles), 2)
        specs = json.loads(a.specialty_json) if a.specialty_json else {}
        n_spec = len([k for k in specs if k != "Unclassified" and k != "Other clinical"])
        a.breadth_score = round(
            min(100.0, (a.unique_titles * 0.4) + (n_spec * 8) + (math.log10(max(a.ebook_posts, 1)) * 10)),
            2,
        )
