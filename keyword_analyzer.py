"""Per-channel keyword frequency analysis from post text and file names."""
from __future__ import annotations

import json
import re
from collections import Counter
from typing import Any

# Stopwords for medical channel keyword extraction (not clinical terms)
STOPWORDS = {
    "the", "and", "for", "with", "this", "that", "from", "your", "you", "are", "was", "have",
    "has", "had", "not", "but", "can", "will", "all", "get", "here", "https", "http", "t.me",
    "telegram", "channel", "download", "free", "pdf", "epub", "edition", "book", "books", "file",
    "join", "subscribe", "link", "click", "share", "contact", "admin", "backup", "posted", "view",
    "step", "enjoy", "device", "google", "drive", "direct", "media", "too", "big", "open", "our",
    "more", "also", "via", "www", "com", "org", "don", "forget", "students", "student", "medical",
    "medicine", "channel", "group", "members", "subscribers",
}

# Preserve clinically meaningful tokens even if short
KEEP_SHORT = {"gp", "ed", "icu", "ecg", "ekg", "mri", "ct", "us", "uk", "au", "amc", "mbs", "pbs",
              "racgp", "fracgp", "fracp", "etg", "bnf", "atls", "acls", "bls", "usmle", "plab",
              "mrcp", "frcr", "ranzcr", "neet", "mbbs", "md", "do", "pa", "np", "ent", "obgyn"}

SPECIALTY_KEYWORDS = {
    "ophthalmology": ["ophthalmology", "ophthalmic", "retina", "glaucoma", "cataract", "eye", "ocular"],
    "radiology": ["radiology", "radiologist", "radiograph", "imaging", "frcr", "ranzcr", "ct", "mri", "ultrasound"],
    "pathology": ["pathology", "histopath", "robbins", "biopsy", "cytopath", "hematopath"],
    "psychiatry": ["psychiatry", "psychiatric", "dsm", "stahl", "psychopharm"],
    "dentistry": ["dental", "dentistry", "odontol", "oral", "maxillofacial"],
    "pharmacy": ["pharmacy", "pharmacist", "pharmacology", "formulary", "pbs", "bnf", "drug"],
    "general_practice": ["general practice", "family medicine", "gp", "primary care", "racgp", "fracgp"],
    "emergency": ["emergency", "trauma", "atls", "tintinalli", "resuscitation", "toxicology"],
    "surgery": ["surgery", "surgical", "operative", "laparoscopic", "orthopedic", "neurosurg"],
    "cardiology": ["cardiology", "cardiac", "heart", "echocardi", "electrophysiol"],
    "endocrine": ["endocrine", "diabetes", "thyroid", "metabolic", "hormone"],
    "australia": ["australia", "australian", "amc", "mbs", "medicare", "pbs", "racgp", "fracgp",
                  "fracp", "ranzcr", "mja", "etg", "medicolegal", "ahpra"],
    "obgyn": ["obstetric", "gynec", "gynaec", "midwif", "neonat"],
    "paediatrics": ["paediatric", "pediatric", "child", "neonat", "infant"],
    "anaesthesia": ["anaesth", "anesthes", "perioperative", "regional block"],
    "wilderness_rural": ["wilderness", "rural", "remote", "tropical medicine", "travel medicine"],
    "medicolegal": ["medicolegal", "malpractice", "forensic", "expert witness"],
    "business_doctors": ["business", "practice management", "billing", "medicare billing"],
    "mbbs_general": ["mbbs", "undergraduate", "anatomy", "physiology", "biochemistry"],
}

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9\-]{1,}(?:\.[a-z]+)?|[a-z]{2}")


def tokenize(text: str) -> list[str]:
    text = text.lower()
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[@#]\w+", " ", text)
    tokens = []
    for m in TOKEN_RE.finditer(text):
        t = m.group(0).strip(".")
        if t in STOPWORDS:
            continue
        if len(t) < 3 and t not in KEEP_SHORT:
            continue
        if t.isdigit():
            continue
        tokens.append(t)
    return tokens


def extract_keywords(posts: list[dict], channel_meta: dict | None = None, top_n: int = 50) -> dict[str, Any]:
    """Return keyword frequencies, specialty tag hits, and top terms."""
    blob_parts = []
    for p in posts:
        blob_parts.append(p.get("text") or "")
        blob_parts.extend(p.get("file_names") or [])
    if channel_meta:
        blob_parts.append(channel_meta.get("title") or "")
        blob_parts.append(channel_meta.get("description") or "")

    full_text = " ".join(blob_parts)
    tokens = tokenize(full_text)
    freq = Counter(tokens)

    # Bigrams from post texts
    words = full_text.lower().split()
    bigrams = Counter()
    for i in range(len(words) - 1):
        w1, w2 = re.sub(r"[^a-z0-9]", "", words[i]), re.sub(r"[^a-z0-9]", "", words[i + 1])
        if w1 in STOPWORDS or w2 in STOPWORDS or len(w1) < 2 or len(w2) < 2:
            continue
        bigrams[f"{w1} {w2}"] += 1

    specialty_hits: dict[str, int] = {}
    text_lower = full_text.lower()
    for spec, kws in SPECIALTY_KEYWORDS.items():
        hits = sum(text_lower.count(k) for k in kws)
        if hits:
            specialty_hits[spec] = hits

    top_unigrams = freq.most_common(top_n)
    top_bigrams = bigrams.most_common(20)

    return {
        "top_keywords_json": json.dumps(top_unigrams[:top_n]),
        "top_bigrams_json": json.dumps(top_bigrams),
        "specialty_keyword_hits_json": json.dumps(dict(sorted(specialty_hits.items(), key=lambda x: -x[1]))),
        "top_keyword_1": top_unigrams[0][0] if top_unigrams else None,
        "top_keyword_1_count": top_unigrams[0][1] if top_unigrams else 0,
        "top_keyword_2": top_unigrams[1][0] if len(top_unigrams) > 1 else None,
        "top_keyword_2_count": top_unigrams[1][1] if len(top_unigrams) > 1 else 0,
        "top_keyword_3": top_unigrams[2][0] if len(top_unigrams) > 2 else None,
        "top_keyword_3_count": top_unigrams[2][1] if len(top_unigrams) > 2 else 0,
        "unique_tokens": len(freq),
        "total_tokens": len(tokens),
    }


def keywords_long_rows(username: str, kw_data: dict[str, Any]) -> list[dict]:
    rows = []
    try:
        items = json.loads(kw_data.get("top_keywords_json") or "[]")
    except json.JSONDecodeError:
        items = []
    for rank, (word, count) in enumerate(items, 1):
        rows.append({
            "channel_key": username.lower(),
            "username": username,
            "rank": rank,
            "keyword": word,
            "count": count,
            "type": "unigram",
        })
    try:
        bigrams = json.loads(kw_data.get("top_bigrams_json") or "[]")
    except json.JSONDecodeError:
        bigrams = []
    for rank, (phrase, count) in enumerate(bigrams, 1):
        rows.append({
            "channel_key": username.lower(),
            "username": username,
            "rank": rank,
            "keyword": phrase,
            "count": count,
            "type": "bigram",
        })
    return rows
