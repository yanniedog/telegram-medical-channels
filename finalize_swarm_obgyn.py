#!/usr/bin/env python3
"""Finalize swarm_obgyn_paeds.json to 25+ verified channels."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

from discover_channels import HEADERS, fetch_channel_meta
from health_relevance import has_books_pdfs_signal
from swarm_obgyn_paeds_search import specialty_tags

OUT = Path("data/agent_swarm/swarm_obgyn_paeds.json")
POSTS = Path("data/posts")
MIN_SUBS = 2000

# Curated seeds from discovery, TGStat, Lyzem, and post-cache evidence
SEEDS = [
    "wafaobgyn", "ob_gyn_books", "obsgynaesonoebook", "pdfchannelgynecologist",
    "Files_of_Pediatrics_and_OBGYN", "obstetricsgynecology1", "Pediatrics1",
    "pediatric_pdfs", "pediatrics_books", "pediatric_books", "pediatricsc",
    "drabdopediatrics", "paedsvideos", "pediatrics1s", "pediatric_materials",
    "pedsurgery", "pediatric_surgery", "jalallah", "pediatrics_course",
    "bscnursing", "kmtcnursing", "nursingpastpapers", "MBS_MedicalBooksStore",
    "medbooksvn2", "million_medical_books", "medical_ebook_pdfs",
    "medicalbooksstoress", "medicalbooksstore55", "medical_library25",
    "medicallibrarymax", "medpdf", "freemedicalbooks", "medical_patna",
    "medicine_way2", "medicinevideoss", "medicalrefrencess", "medicalprep",
    "medipoints", "boards_beyonds", "usmlebooks", "usmlestore", "plab_mrcp",
    "sketchymedical", "internalmedicinebookss", "sdgtbookstore", "medmaterialx",
    "mmedicalbookss", "booksmedicospdf", "medbookspdf", "pdf4yo",
    "medical_free_ebooks", "medicalbookspdfs", "Prometric", "surgery_6",
    "obgyn_books", "gynecology_books", "obstetrics_books", "neonatology_books",
    "midwifery_books", "neonatal_books", "paediatrics_books", "paediatric_books",
    "obgyn_library", "pediatrics_library", "neonatology_library", "midwifery_library",
    "obgyn_ebooks", "pediatrics_ebooks", "obgyn_medical_books", "pediatric_medical_books",
    "obgyn_textbooks", "pediatric_textbooks", "midwifery_textbooks",
    "obgyn_handbook", "pediatric_handbook", "neonatal_handbook",
    "obgyn_mcqs", "pediatric_mcqs", "obgyn_notes", "pediatrics_notes",
    "neonatology_notes", "midwifery_notes", "obgyn_and_pediatrics", "obs_gyn_paeds",
    "gyn_obs_books", "obstetrics_gynaecology_books", "paediatrics_neonatology",
    "nicu_books", "obgynbookstore", "pediatricbookstore",
    "ginecologia_obstetricia", "pediatria_libros", "neonatologia_pdf",
    "obstetricia_libros", "ginecologia_libros", "obgynworld", "pediatricworld",
    "internalmedcine", "obstetrics_gynecology", "pediatrics_channel",
    "neonatology_channel", "midwifery_channel", "obgyn_channel",
    "pediatric_nursing", "obgyn_nursing", "nursing_books_pdf", "nursingbooks",
    "obgyn_pdf_books", "pediatric_pdf_books", "paediatric_pdf_books",
    "neonatology_pdf_books", "midwifery_pdf_books", "obgynpdf", "pediatricspdf",
    "paediatricspdf", "neonatologypdf", "midwiferypdf", "obgynbooks", "pediatricsbooks",
    "neonatologybooks", "midwiferybooks", "obgynlibrary", "pediatricslibrary",
    "neonatologylibrary", "midwiferylibrary", "obgynmedicalbooks", "pediatricsmedicalbooks",
    "neonatologymedicalbooks", "midwiferymedicalbooks", "obgynbookspdf",
    "pediatricsbookspdf", "neonatologybookspdf", "midwiferybookspdf",
]

FALSE_POSITIVE = {"laboratory_books"}  # "labor" in laboratory matched midwifery

PDF_IN_POSTS = re.compile(r"\.(pdf|epub|djvu|mobi)\b", re.I)
SPECIALTY_IN_POSTS = re.compile(
    r"obgyn|ob[\s_-]?gyn|gynec|gynaec|obstet|paediatr|pediatr|neonat|midwif|"
    r"maternal|fetal|perinat|nicu|child health|williams obstet|nelson pediat",
    re.I,
)


def posts_have_books_and_specialty(username: str) -> bool:
    p = POSTS / f"{username.lower()}.json"
    if not p.exists():
        return False
    try:
        posts = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    has_pdf = False
    has_spec = False
    for post in posts[:200]:
        blob = json.dumps(post, ensure_ascii=False)
        if PDF_IN_POSTS.search(blob):
            has_pdf = True
        if SPECIALTY_IN_POSTS.search(blob):
            has_spec = True
        if has_pdf and has_spec:
            return True
    return has_pdf and SPECIALTY_IN_POSTS.search(username, re.I)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if OUT.exists():
        for e in json.loads(OUT.read_text(encoding="utf-8")):
            existing[e["username"].lower()] = e

    results: dict[str, dict] = {
        k: v for k, v in existing.items() if k not in FALSE_POSITIVE
    }

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for uname in SEEDS:
            key = uname.lower()
            if key in results:
                continue
            meta = fetch_channel_meta(client, uname)
            if meta.get("error"):
                continue
            subs = meta.get("subscribers") or 0
            if subs < MIN_SUBS:
                continue
            title = meta.get("title") or ""
            desc = meta.get("description") or ""
            tags = specialty_tags(uname, title, desc)
            if not tags:
                continue
            books_meta = has_books_pdfs_signal(uname, title, desc)
            books_posts = posts_have_books_and_specialty(uname)
            if not books_meta and not books_posts:
                continue
            results[key] = {
                "username": key,
                "subscribers_estimate": subs,
                "specialty_tags": tags,
                "has_direct_ebooks": True,
                "source_url": f"https://t.me/{key}",
            }
            print(f"add {key} {subs} {tags}", flush=True)

    final = sorted(results.values(), key=lambda x: -x["subscribers_estimate"])
    OUT.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(final)} channels", flush=True)


if __name__ == "__main__":
    main()
