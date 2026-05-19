#!/usr/bin/env python3
"""Search OBGYN/paeds/neonatology/midwifery book channels for swarm JSON."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import httpx

from discover_channels import fetch_channel_meta, scrape_lyzem_page
from health_relevance import has_books_pdfs_signal

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
MIN_SUBS = 2000
OUT = Path("data/agent_swarm/swarm_obgyn_paeds.json")
ALLOWED = frozenset({"obgyn", "gynecology", "obstetrics", "paediatrics", "neonatology", "midwifery"})

SPECIALTY_RE = re.compile(
    r"obgyn|ob[\s_-]?gyn|gynec|gynaec|obstet|paediatr|pediatr|neonat|midwif|"
    r"perinat|maternal|fetal|child health|nicu|nursery|peds?\b|paeds?\b",
    re.I,
)

QUERIES = [
    "obstetrics gynecology books telegram",
    "obgyn books pdf telegram",
    "gynecology books pdf channel",
    "obstetrics textbooks telegram",
    "paediatrics pediatrics books pdf",
    "pediatric books pdf telegram",
    "neonatology books channel",
    "neonatology pdf telegram",
    "midwifery books pdf telegram",
    "midwifery textbooks channel",
    "ob gyn books pdf",
    "pediatrics ebooks telegram",
    "paediatric books library",
    "obstetric gynecologic books",
    "williams obstetrics pdf",
    "nelson pediatrics pdf telegram",
    "gynecology obstetrics mcq books",
    "neonatal resuscitation books pdf",
    "perinatal medicine books telegram",
    "maternal fetal medicine books",
    "nursing midwifery books pdf",
    "pediatric nursing books telegram",
    "obstetrics nursing books pdf",
    "child health books pdf telegram",
    "fetal medicine books channel",
    "ginecologia obstetricia libros pdf",
    "pediatria libros pdf telegram",
    "obstetricia ginecologia canal",
    "neonatologia libros pdf",
    "obgyn medical books pdf",
    "pediatric medical library telegram",
    "obsgynaesonoebook",
    "pediatricsc books courses",
    "drabdopediatrics",
    "Files_of_Pediatrics_and_OBGYN",
    "pediatric_books neonatology",
    "MBS_MedicalBooksStore pediatrics",
    "Prometric obgyn midwifery",
    "nursingpastpapers midwifery",
]

SEED_HANDLES = [
    "wafaobgyn", "ob_gyn_books", "obsgynaesonoebook", "pediatric_pdfs", "pediatrics_books",
    "pediatric_books", "pediatricsc", "drabdopediatrics", "Files_of_Pediatrics_and_OBGYN",
    "MBS_MedicalBooksStore", "Prometric",
    "obgyn_books", "obgynbooks", "gynecology_books", "gynecologybooks",
    "obstetrics_books", "obstetricsbooks", "obstetric_books", "pediatric_books",
    "paediatrics_books", "paediatric_books", "paediatric_pdfs", "pediatricbooks",
    "paediatricsbooks", "neonatology_books", "neonatologybooks", "neonatal_books",
    "neonatalbooks", "midwifery_books", "midwiferybooks", "midwifery_pdfs",
    "obgyn_pdf", "obgynpdfs", "gyn_books", "gynbooks", "peds_books", "pedsbooks",
    "pediatric_library", "pediatrics_library", "obgyn_library", "gynecology_library",
    "obstetrics_library", "neonatology_library", "midwifery_library",
    "obgyn_medical_books", "pediatric_medical_books", "obgyn_ebooks",
    "pediatric_ebooks", "obstetrics_gynecology_books", "obstetricsandgynecology",
    "pediatric_medicine_books", "neonatal_medicine", "midwifery_notes",
    "obgyn_notes", "pediatrics_notes", "pedsurgery", "pediatric_surgery",
    "bscnursing", "kmtcnursing", "nursingpastpapers", "nursing_books_pdf",
    "nursingbooks", "pediatric_nursing", "obgyn_nursing",
    "obgyn_textbooks", "pediatric_textbooks", "midwifery_textbooks",
    "obgyn_handbook", "pediatric_handbook", "neonatal_handbook",
    "obgyn_atlas", "pediatric_atlas", "fetal_ultrasound_books",
    "obstetric_ultrasound", "gynecologic_surgery_books", "pediatric_surgery_books",
    "high_risk_obstetrics", "pediatric_emergency_books", "neonatal_emergency",
    "obgyn_oncology", "gynecologic_oncology", "reproductive_medicine_books",
    "infertility_books", "maternal_child_health", "child_health_books",
    "perinatal_books", "obgyn_mcqs", "pediatric_mcqs", "neonatal_nursing",
    "obgyn_and_pediatrics", "obs_gyn_paeds", "obgyn_paeds_books",
    "gyn_obs_books", "obstetrics_gynaecology_books", "paediatrics_neonatology",
    "nicu_books", "obgynbookstore", "pediatricbookstore",
    "ginecologia_obstetricia", "pediatria_pdf", "neonatologia_pdf",
    "obstetricia_libros", "ginecologia_libros", "obgynworld", "pediatricworld",
    "obgyn_channel", "pediatrics_channel", "gynecology_channel",
    "obstetrics_channel", "neonatology_pdf", "obgyn_pdf_books",
    "pediatric_pdf_books", "obgyn_clinical", "pediatric_clinical",
    "obgyn_lectures", "pediatric_lectures", "obgyn_videos_books",
    "pediatrics_videos_books", "obgyn_review", "pediatrics_review",
    "neonatology_review", "obgyn_mbbs", "pediatrics_mbbs",
    "obgyn_notes_pdf", "pediatrics_notes_pdf", "neonatology_notes_pdf",
    "midwifery_notes_pdf", "obgyn_apuntes", "pediatria_libros",
    "parto_puerperio_books", "embarazo_books", "pediatria_libros_pdf",
    "obgyn_residency", "pediatrics_residency", "neonatology_residency",
    "obgyn_usmle", "pediatrics_usmle", "obgyn_plab", "pediatrics_plab",
    "obgyn_mrcp", "pediatrics_mrcp", "obgyn_neet", "pediatrics_neet",
    "obgyn_amc", "pediatrics_amc", "obgyn_final_year", "pediatrics_final_year",
    "obgyn_pg", "pediatrics_pg", "obgyn_dnb", "pediatrics_dnb",
    "obgyn_fmge", "pediatrics_fmge", "obgyn_inicet", "pediatrics_inicet",
    "obgyn_boards", "pediatrics_boards", "neonatology_boards",
    "obgyn_cases", "pediatric_cases", "obgyn_surgery", "gynecologic_surgery",
    "obstetric_surgery", "pediatric_cardiology_books", "pediatric_neurology_books",
    "obgyn_endocrinology", "obgyn_radiology", "pediatric_radiology_books",
    "obgyn_ultrasound_books", "fetal_medicine", "maternal_medicine",
    "child_medicine_books", "obgyn_ivf", "pediatric_endocrinology",
    "pediatric_gastroenterology", "pediatric_pulmonology",
    "medicalbooksstoress", "million_medical_books", "medical_ebook_pdfs",
    "medbooksvn2", "medical_library25", "medpdf", "medicalbooksstorea",
    "medicalbooksstore55", "medical_books_storess", "medicallibrarymax",
    "freemedicalbooks", "medicalprep", "medical_patna", "medicine_way2",
    "medicinevideoss", "medicalrefrencess", "sketchymedical", "medipoints",
    "boards_beyonds", "usmlebooks", "usmlestore", "usmlestep1233",
    "plab_mrcp", "mccqe_1", "nbme_q", "medstudyvideos",
    "internalmedicinebookss", "sdgtbookstore", "medmaterialx", "mmedicalbookss",
    "booksmedicospdf", "medbookspdf", "pdf4yo", "pezeshkibooks",
    "medicalbooksstore55", "medical_free_ebooks", "medicalbookspdfs",
    "medicalbookshare", "medical_e_books", "medicinestore", "medusmle",
    "medical_book772", "medicalusmle_videos", "medical_ebooks_library",
    "medicalbooksstorebot", "medical_books_store", "medbookschannel",
    "medbooks_pdf", "medbookschannel1", "medbooksstore", "medbookstore",
    "medbookslibrary", "medbookslibrary1", "medbookspdf1", "medbookspdf2",
    "obgynbooks1", "pediatricsbooks1", "neonatologybooks1", "midwiferybooks1",
    "obgynbooks2", "pediatricsbooks2", "obgynpdf", "pediatricspdf",
    "paediatricspdf", "neonatologypdf", "midwiferypdf", "obgynlibrary",
    "pediatricslibrary", "neonatologylibrary", "midwiferylibrary",
    "obgynmedical", "pediatricsmedical", "neonatologymedical", "midwiferymedical",
    "obgynstore", "pediatricsstore", "neonatologystore", "midwiferystore",
    "obgynfree", "pediatricsfree", "neonatologyfree", "midwiferyfree",
    "obgynpdfbooks", "pediatricspdfbooks", "paediatricspdfbooks",
    "neonatologypdfbooks", "midwiferypdfbooks", "obgyn_ebook", "pediatrics_ebook",
    "paediatrics_ebook", "neonatology_ebook", "midwifery_ebook",
    "obgyn_ebooks", "pediatrics_ebooks", "paediatrics_ebooks",
    "neonatology_ebooks", "midwifery_ebooks", "obgynbookschannel",
    "pediatricsbookschannel", "neonatologybookschannel", "midwiferybookschannel",
    "obgynbookchannel", "pediatricsbookchannel", "neonatologybookchannel",
    "midwiferybookchannel", "obgynbookpdf", "pediatricsbookpdf",
    "neonatologybookpdf", "midwiferybookpdf", "obgynbookspdf",
    "pediatricsbookspdf", "neonatologybookspdf", "midwiferybookspdf",
    "obgynmedbooks", "pediatricsmedbooks", "neonatologymedbooks",
    "midwiferymedbooks", "obgynmedicalbooks", "pediatricsmedicalbooks",
    "neonatologymedicalbooks", "midwiferymedicalbooks",
]


def specialty_tags(username: str, title: str = "", description: str = "") -> list[str]:
    blob = f"{username} {title} {description}".lower()
    tags: list[str] = []
    if re.search(r"obgyn|ob[\s_-]?gyn|gynec|gynaec|obstet|maternal|fetal|perinat|reproductive|infertil|ivf", blob, re.I):
        tags.append("obgyn")
        if re.search(r"gynec|gynaec", blob, re.I):
            tags.append("gynecology")
        if re.search(r"obstet", blob, re.I):
            tags.append("obstetrics")
    if re.search(r"paediatr|pediatr|child health|peds?\b|paeds?\b|child medic|pediatric", blob, re.I):
        tags.append("paediatrics")
    if re.search(r"neonat|nicu|newborn|perinatal", blob, re.I):
        tags.append("neonatology")
    if re.search(r"midwif|labor|labour|delivery|puerper|parto|embaraz", blob, re.I):
        tags.append("midwifery")
    if re.search(r"nursing", blob, re.I) and re.search(r"midwif|obstet|maternal|paediatr|pediatr|neonat", blob, re.I):
        if re.search(r"midwif|obstet|maternal|labor", blob, re.I):
            tags.append("midwifery")
        if re.search(r"paediatr|pediatr|neonat|child", blob, re.I):
            tags.append("paediatrics")
    return sorted(t for t in set(tags) if t in ALLOWED)


def matches_specialty(username: str, title: str = "", description: str = "") -> bool:
    return bool(SPECIALTY_RE.search(f"{username} {title} {description}"))


def load_existing_meta() -> dict:
    meta: dict = {}
    dc = Path("data/discovered_channels.json")
    if dc.exists():
        raw = json.loads(dc.read_text(encoding="utf-8"))
        meta.update(raw.get("all", {}))
        meta.update(raw.get("qualified", {}))
    merged = Path("data/agent_discoveries_merged.json")
    if merged.exists():
        for e in json.loads(merged.read_text(encoding="utf-8")):
            u = e["username"].lower()
            if u not in meta:
                meta[u] = {
                    "username": e["username"],
                    "subscribers": e.get("subscribers_estimate"),
                    "title": "",
                    "description": "",
                    "agent_specialty_tags": e.get("specialty_tags", []),
                }
    return meta


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    seen: set[str] = set()
    existing = load_existing_meta()

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for q in QUERIES:
            for page in range(1, 8):
                for h in scrape_lyzem_page(client, q, page):
                    seen.add(h.lower())
                time.sleep(0.25)
            time.sleep(0.3)

        for h in SEED_HANDLES:
            seen.add(h.lower())
        for u, m in existing.items():
            if matches_specialty(u, m.get("title", ""), m.get("description", "")):
                seen.add(u.lower())

        print(f"handles to check: {len(seen)}", flush=True)
        results: list[dict] = []
        for i, uname in enumerate(sorted(seen)):
            meta = existing.get(uname)
            if not meta or not meta.get("subscribers") or meta.get("error"):
                meta = fetch_channel_meta(client, uname)
                time.sleep(0.2)
            if meta.get("error"):
                continue
            subs = meta.get("subscribers") or 0
            if subs < MIN_SUBS:
                continue
            title = meta.get("title") or ""
            desc = meta.get("description") or ""
            if not has_books_pdfs_signal(uname, title, desc):
                continue
            tags = specialty_tags(uname, title, desc)
            if not tags:
                continue
            results.append({
                "username": uname,
                "subscribers_estimate": subs,
                "specialty_tags": sorted(set(tags)),
                "has_direct_ebooks": True,
                "source_url": f"https://t.me/{uname}",
            })
            if len(results) % 5 == 0:
                print(f"qualified so far: {len(results)}", flush=True)
            if (i + 1) % 50 == 0:
                print(f"checked {i+1}/{len(seen)}", flush=True)

    by_user: dict[str, dict] = {}
    for r in results:
        by_user[r["username"].lower()] = r
    final = sorted(by_user.values(), key=lambda x: x["subscribers_estimate"], reverse=True)
    OUT.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(final)} channels to {OUT}", flush=True)


if __name__ == "__main__":
    main()
