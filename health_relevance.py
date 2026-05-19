"""Broad health/medicine relevance scoring for Telegram channels (inclusive)."""
from __future__ import annotations

import re

BOOKS_PDFS_RE = re.compile(
    r"books?|pdfs?|ebooks?|epubs?|libros|libri|kitap|livres|bucher|textbook|"
    r"bookstore|bookshop|medbook|ebook|library|biblioteca|ketab|pezeshki|medico",
    re.I,
)

HEALTH_RE = re.compile(
    r"medical|medicine|medic\b|health|surgery|surgical|nurs|pharm|pharma|dent|dental|"
    r"doctor|physician|clinic|hospital|anatomy|physiol|pathol|biochem|microbio|"
    r"radiolog|imaging|psychiat|psycholog|neurol|neurosurg|cardio|cardiol|"
    r"pediatr|paediatr|gynec|gynaec|obstet|midwif|anaesth|anesthes|emerg|trauma|"
    r"orthop|urolog|dermat|ophthalm|optometr|\bent\b|otolaryng|pulmon|respirat|"
    r"nephro|renal|gastro|hepat|endocrin|diabet|rheumat|hematol|oncolog|"
    r"infectious|immunol|geriatr|critical care|\bicu\b|pain medicine|"
    r"wilderness|rural medicine|tropical medicine|travel medicine|"
    r"nutrition|dietetic|dietitian|wellness|public health|epidemiol|"
    r"physio|physiotherap|rehab|occupational therapy|paramedic|ambulan|"
    r"laboratory|lab tech|histolog|cyto|genetic|biomed|life sci|"
    r"mbbs|mbchb|usmle|plab|mrcp|amc|racgp|fracgp|fracp|mccqe|neet|"
    r"usmle|board exam|clinical|therapeutic|formulary|mbs|pbs|medicare|"
    r"medicolegal|forensic medicine|veterinar|animal health|vet med|"
    r"chiropractic|osteopath|acupuncture|homeopath|ayurved|traditional medicine|"
    r"anesthesia|perioperative|intensive|residency|fellowship|"
    r"gray'?s|harrison|robbins|netter|sabiston|bailey",
    re.I,
)

NON_HEALTH_BLOCK = re.compile(
    r"crypto|bitcoin|forex|casino|betting|poker|movie|film|novel|fiction|"
    r"comic|manga|anime|recipe|cooking|garden(?!ing therapy)|fashion|makeup|"
    r"beauty tips|music album|song lyrics|programming|python tutorial|"
    r"javascript|marketing ebook(?! medicine)|business ebook(?! medicine)",
    re.I,
)


def has_books_pdfs_signal(username: str, title: str = "", description: str = "") -> bool:
    blob = f"{username} {title} {description}"
    return bool(BOOKS_PDFS_RE.search(blob))


def health_relevance_score(username: str, title: str = "", description: str = "") -> tuple[int, list[str]]:
    """Return 0-100 score and matched reason tags."""
    blob = f"{username} {title} {description}"
    if NON_HEALTH_BLOCK.search(blob) and not HEALTH_RE.search(blob):
        return 0, ["blocked_non_health"]
    reasons: list[str] = []
    score = 0
    if has_books_pdfs_signal(username, title, description):
        score += 25
        reasons.append("books_pdfs_in_name")
    for m in HEALTH_RE.finditer(blob):
        tag = m.group(0).lower()[:40]
        if tag not in reasons:
            reasons.append(tag)
        score += 8
    score = min(100, score)
    if score >= 20 and has_books_pdfs_signal(username, title, description):
        score = max(score, 40)
    return score, reasons


def include_in_health_workbook(meta: dict, min_subs: int = 2000) -> bool:
    """Inclusive: books/pdfs/library channels + any health signal."""
    u = (meta.get("username") or "").lower()
    title = meta.get("title") or ""
    desc = meta.get("description") or ""
    subs = meta.get("subscribers") or 0
    if u in {"nachrichtenportal", "combot", "durov", "tgstat", "lyzem", "telegram"}:
        return False
    if meta.get("agent_health_relevant") is True:
        return subs >= min_subs or subs == 0
    if meta.get("agent_specialty_tags"):
        return True
    score, reasons = health_relevance_score(u, title, desc)
    if "blocked_non_health" in reasons:
        return False
    if score >= 10:
        return True
    if has_books_pdfs_signal(u, title, desc) and subs >= min_subs:
        return True
    if subs >= min_subs and HEALTH_RE.search(f"{title} {desc} {u}"):
        return True
    return False
