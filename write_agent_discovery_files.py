#!/usr/bin/env python3
"""Write subagent discovery JSON files (one-time bundle from parallel agent runs)."""
import json
from pathlib import Path

DATA = Path("data")
DATA.mkdir(exist_ok=True)

BUNDLES = {
    "agent_au.json": [
        {"username": "amcmcq", "subscribers_estimate": 9674, "specialty_tags": ["australia", "amc", "img"], "has_direct_ebooks": True, "source_url": "https://t.me/amcmcq"},
        {"username": "amedexltd", "subscribers_estimate": 7002, "specialty_tags": ["australia", "amc", "medicolegal"], "has_direct_ebooks": True, "source_url": "https://t.me/amedexltd"},
        {"username": "imd_app", "subscribers_estimate": 45954, "specialty_tags": ["australia", "etg", "amc"], "has_direct_ebooks": False, "source_url": "https://t.me/IMD_App"},
        {"username": "medic_store", "subscribers_estimate": 13895, "specialty_tags": ["australia", "etg", "mbs", "pbs"], "has_direct_ebooks": False, "source_url": "https://t.me/Medic_Store"},
        {"username": "amcclinical", "subscribers_estimate": 4802, "specialty_tags": ["australia", "amc_clinical"], "has_direct_ebooks": True, "source_url": "https://t.me/AMCclinical"},
        {"username": "amcclinicalexamprep", "subscribers_estimate": 3774, "specialty_tags": ["australia", "amc_clinical"], "has_direct_ebooks": True, "source_url": "https://t.me/amcclinicalexamprep"},
        {"username": "amcmcqrecalls", "subscribers_estimate": 5631, "specialty_tags": ["australia", "amc_mcq"], "has_direct_ebooks": True, "source_url": "https://t.me/amcmcqrecalls"},
    ],
    "agent_surgery.json": [
        {"username": "freesurgerybooks28", "subscribers_estimate": 35855, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/freesurgerybooks28"},
        {"username": "surgeryvideos", "subscribers_estimate": 82621, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/surgeryvideos"},
        {"username": "medicalbooksstoress", "subscribers_estimate": 59208, "specialty_tags": ["surgery", "general"], "has_direct_ebooks": True, "source_url": "https://t.me/MedicalBooksStoress"},
        {"username": "million_medical_books", "subscribers_estimate": 95420, "specialty_tags": ["surgery", "general"], "has_direct_ebooks": True, "source_url": "https://t.me/Million_medical_books"},
        {"username": "medpdf", "subscribers_estimate": 21787, "specialty_tags": ["surgery", "mbbs"], "has_direct_ebooks": True, "source_url": "https://t.me/medpdf"},
        {"username": "surgerynb", "subscribers_estimate": 14648, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/SurgeryNB"},
        {"username": "thesurgerytimes", "subscribers_estimate": 13709, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/thesurgerytimes"},
        {"username": "surgerybyhamoud", "subscribers_estimate": 13595, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/surgerybyhamoud"},
        {"username": "uroresources", "subscribers_estimate": 20852, "specialty_tags": ["urology"], "has_direct_ebooks": True, "source_url": "https://t.me/uroresources"},
        {"username": "orthobooksandlectures", "subscribers_estimate": 20707, "specialty_tags": ["orthopedics"], "has_direct_ebooks": True, "source_url": "https://t.me/orthobooksandlectures"},
        {"username": "uro_first", "subscribers_estimate": 11970, "specialty_tags": ["urology"], "has_direct_ebooks": True, "source_url": "https://t.me/uro_first"},
        {"username": "pedsurgery", "subscribers_estimate": 7445, "specialty_tags": ["pediatric_surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/pedsurgery"},
        {"username": "gastrointestinal_books", "subscribers_estimate": 7197, "specialty_tags": ["hepatobiliary", "colorectal"], "has_direct_ebooks": True, "source_url": "https://t.me/gastrointestinal_books"},
        {"username": "orthopedic_book", "subscribers_estimate": 7140, "specialty_tags": ["orthopedics"], "has_direct_ebooks": True, "source_url": "https://t.me/orthopedic_book"},
        {"username": "neurobank_books", "subscribers_estimate": 6982, "specialty_tags": ["neurosurgery"], "has_direct_ebooks": True, "source_url": "https://t.me/neurobank_books"},
        {"username": "surgery_pdf_books", "subscribers_estimate": 5245, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/surgery_pdf_books"},
        {"username": "surgery_6", "subscribers_estimate": 5337, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/surgery_6"},
        {"username": "cardiobooks", "subscribers_estimate": 4517, "specialty_tags": ["cardiothoracic"], "has_direct_ebooks": True, "source_url": "https://t.me/cardiobooks"},
        {"username": "surgerycollection", "subscribers_estimate": 4044, "specialty_tags": ["surgery"], "has_direct_ebooks": True, "source_url": "https://t.me/surgerycollection"},
    ],
    "agent_radiology_pathology.json": [
        {"username": "pathologybooks", "subscribers_estimate": 39595, "specialty_tags": ["pathology"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@pathology_mcqs"},
        {"username": "radiologiaenpdf", "subscribers_estimate": 21315, "specialty_tags": ["radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/radiologiaenpdf"},
        {"username": "radiologist_library", "subscribers_estimate": 15746, "specialty_tags": ["radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/Radiologist_Library"},
        {"username": "radiology_ebooks", "subscribers_estimate": 13790, "specialty_tags": ["radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/radiology_ebooks"},
        {"username": "radiologygoldenbooks", "subscribers_estimate": 12159, "specialty_tags": ["radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/radiologygoldenbooks"},
        {"username": "mcqradiology", "subscribers_estimate": 8584, "specialty_tags": ["radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/mcqradiology"},
        {"username": "patho_videos", "subscribers_estimate": 6706, "specialty_tags": ["pathology"], "has_direct_ebooks": True, "source_url": "https://t.me/Patho_Videos"},
        {"username": "medbookspdf", "subscribers_estimate": 3831, "specialty_tags": ["pathology", "radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/medbookspdf"},
        {"username": "sketchymedical", "subscribers_estimate": 89811, "specialty_tags": ["pathology", "microbiology"], "has_direct_ebooks": True, "source_url": "https://t.me/sketchymedical"},
        {"username": "medicalrefrencess", "subscribers_estimate": 50254, "specialty_tags": ["pathology", "radiology"], "has_direct_ebooks": True, "source_url": "https://t.me/medicalrefrencess"},
    ],
    "agent_psych_gp_em.json": [
        {"username": "psychiatrylibrarybooks", "subscribers_estimate": 19797, "specialty_tags": ["psychiatry"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@psychiatrylibrarybooks"},
        {"username": "psychiatry_vid", "subscribers_estimate": 22209, "specialty_tags": ["psychiatry"], "has_direct_ebooks": True, "source_url": "https://t.me/psychiatry_vid"},
        {"username": "dsm_5", "subscribers_estimate": 5730, "specialty_tags": ["psychiatry", "dsm"], "has_direct_ebooks": True, "source_url": "https://t.me/s/DSM_5"},
        {"username": "medipoints", "subscribers_estimate": 73442, "specialty_tags": ["neurology", "gp"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@medipoints"},
        {"username": "maragia", "subscribers_estimate": 11000, "specialty_tags": ["gp", "emergency"], "has_direct_ebooks": True, "source_url": "https://t.me/s/maragia"},
        {"username": "urgenciasyemergencias", "subscribers_estimate": 15074, "specialty_tags": ["emergency"], "has_direct_ebooks": False, "source_url": "https://tgstat.com/channel/@urgenciasyemergencias"},
        {"username": "bibliomed02", "subscribers_estimate": 9419, "specialty_tags": ["gp", "general"], "has_direct_ebooks": True, "source_url": "https://t.me/bibliomed02"},
    ],
    "agent_dental_pharm_eye.json": [
        {"username": "thedentists", "subscribers_estimate": 50507, "specialty_tags": ["dentistry"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@thedentists"},
        {"username": "libraryedent", "subscribers_estimate": 54397, "specialty_tags": ["dentistry"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@LibraryEDent"},
        {"username": "dentist_book", "subscribers_estimate": 31699, "specialty_tags": ["dentistry"], "has_direct_ebooks": True, "source_url": "https://t.me/dentist_book"},
        {"username": "bdsmdsdentalbooks", "subscribers_estimate": 31327, "specialty_tags": ["dentistry"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@bdsmdsdentalbooks"},
        {"username": "dental_den", "subscribers_estimate": 20069, "specialty_tags": ["dentistry"], "has_direct_ebooks": True, "source_url": "https://t.me/dental_den"},
        {"username": "pharmabookscollection", "subscribers_estimate": 44846, "specialty_tags": ["pharmacy"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@pharmabookscollection"},
        {"username": "pharmacy_sources", "subscribers_estimate": 17037, "specialty_tags": ["pharmacy"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@Pharmacy_sources"},
        {"username": "ophthalmology_books_2016", "subscribers_estimate": 60869, "specialty_tags": ["ophthalmology"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@Ophthalmology_Books_2016"},
        {"username": "ophthbooks", "subscribers_estimate": 8950, "specialty_tags": ["ophthalmology"], "has_direct_ebooks": False, "source_url": "https://t.me/OphthBooks"},
        {"username": "iamoptolibrary", "subscribers_estimate": 6623, "specialty_tags": ["ophthalmology"], "has_direct_ebooks": True, "source_url": "https://t.me/iamoptolibrary"},
        {"username": "entvideos", "subscribers_estimate": 35914, "specialty_tags": ["ent"], "has_direct_ebooks": True, "source_url": "https://t.me/ENTVideos"},
    ],
    "agent_internal_medicine.json": [
        {"username": "medicine_way2", "subscribers_estimate": 124223, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://t.me/Medicine_Way2"},
        {"username": "medicinevideoss", "subscribers_estimate": 109288, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@medicinevideoss"},
        {"username": "medical_patna", "subscribers_estimate": 42630, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://t.me/Medical_Patna"},
        {"username": "lraq_ed", "subscribers_estimate": 17611, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://t.me/lraq_ed"},
        {"username": "medicalbooksstore55", "subscribers_estimate": 16571, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://t.me/MedicalBooksStore55"},
        {"username": "cardiology_premium_videos", "subscribers_estimate": 14912, "specialty_tags": ["cardiology"], "has_direct_ebooks": True, "source_url": "https://t.me/Cardiology_premium_videos"},
        {"username": "internalmedicinebookss", "subscribers_estimate": 8318, "specialty_tags": ["internal_medicine"], "has_direct_ebooks": True, "source_url": "https://t.me/InternalMedicineBookss"},
        {"username": "hematologys", "subscribers_estimate": 8659, "specialty_tags": ["hematology"], "has_direct_ebooks": True, "source_url": "https://t.me/Hematologys"},
        {"username": "dialibrary", "subscribers_estimate": 5816, "specialty_tags": ["endocrinology", "diabetes"], "has_direct_ebooks": True, "source_url": "https://t.me/dialibrary"},
        {"username": "nephrotube", "subscribers_estimate": 5124, "specialty_tags": ["nephrology"], "has_direct_ebooks": True, "source_url": "https://t.me/NephroTube"},
        {"username": "pulmonaryc", "subscribers_estimate": 3658, "specialty_tags": ["pulmonology"], "has_direct_ebooks": True, "source_url": "https://t.me/pulmonaryc"},
        {"username": "micromls1", "subscribers_estimate": 6026, "specialty_tags": ["infectious_disease"], "has_direct_ebooks": True, "source_url": "https://t.me/MicroMLS1"},
        {"username": "gastroenterology_courses", "subscribers_estimate": 2189, "specialty_tags": ["gastroenterology"], "has_direct_ebooks": True, "source_url": "https://t.me/gastroenterology_courses"},
    ],
    "agent_mbbs_general.json": [
        {"username": "medical_library25", "subscribers_estimate": 14372, "specialty_tags": ["mbbs"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@medical_library25"},
        {"username": "freemedicalbooks", "subscribers_estimate": 6536, "specialty_tags": ["mbbs"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@freemedicalbooks"},
        {"username": "medmaterialx", "subscribers_estimate": 4636, "specialty_tags": ["mbbs"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@medmaterialx"},
        {"username": "mmedicalbookss", "subscribers_estimate": 2743, "specialty_tags": ["mbbs"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@mmedicalbookss"},
    ],
    "agent_dermatology_nursing.json": [
        {"username": "newdermbooks", "subscribers_estimate": 14717, "specialty_tags": ["dermatology"], "has_direct_ebooks": True, "source_url": "https://t.me/newdermbooks"},
        {"username": "sdgtbookstore", "subscribers_estimate": 35742, "specialty_tags": ["dermatology"], "has_direct_ebooks": True, "source_url": "https://t.me/sdgtbookstore"},
        {"username": "bscnursing", "subscribers_estimate": 49848, "specialty_tags": ["nursing"], "has_direct_ebooks": True, "source_url": "https://t.me/Bscnursing"},
        {"username": "kmtcnursing", "subscribers_estimate": 11121, "specialty_tags": ["nursing"], "has_direct_ebooks": True, "source_url": "https://t.me/kmtcnursing"},
        {"username": "fisioterapiapdf", "subscribers_estimate": 25535, "specialty_tags": ["physiotherapy"], "has_direct_ebooks": True, "source_url": "https://t.me/fisioterapiapdf"},
        {"username": "fisioterapiaykinesiologia", "subscribers_estimate": 42980, "specialty_tags": ["physiotherapy"], "has_direct_ebooks": True, "source_url": "https://t.me/FisioterapiayKinesiologia"},
        {"username": "plab_mrcp", "subscribers_estimate": 69340, "specialty_tags": ["plab", "mrcp"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@Plab_MRcp"},
        {"username": "mrcp2024", "subscribers_estimate": 6220, "specialty_tags": ["mrcp"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@mrcp2024"},
        {"username": "usmlestep1233", "subscribers_estimate": 30432, "specialty_tags": ["usmle"], "has_direct_ebooks": True, "source_url": "https://t.me/usmlestep1233"},
        {"username": "usmlestore", "subscribers_estimate": 21741, "specialty_tags": ["usmle"], "has_direct_ebooks": True, "source_url": "https://t.me/usmlestore"},
        {"username": "usmlestep_1_2", "subscribers_estimate": 25419, "specialty_tags": ["usmle"], "has_direct_ebooks": True, "source_url": "https://t.me/Usmlestep_1_2"},
    ],
    "agent_obgyn_paeds_anaes.json": [
        {"username": "wafaobgyn", "subscribers_estimate": 33759, "specialty_tags": ["obgyn"], "has_direct_ebooks": True, "source_url": "https://t.me/wafaobgyn"},
        {"username": "ob_gyn_books", "subscribers_estimate": 6008, "specialty_tags": ["obgyn"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@ob_gyn_books"},
        {"username": "pediatric_pdfs", "subscribers_estimate": 8501, "specialty_tags": ["paediatrics"], "has_direct_ebooks": True, "source_url": "https://t.me/pediatric_pdfs"},
        {"username": "pediatrics_books", "subscribers_estimate": 4254, "specialty_tags": ["paediatrics"], "has_direct_ebooks": True, "source_url": "https://t.me/pediatrics_books"},
        {"username": "anesthesia_books_pdf", "subscribers_estimate": 4259, "specialty_tags": ["anaesthesia"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@anesthesia_books_pdf"},
        {"username": "critical_care_books", "subscribers_estimate": 2924, "specialty_tags": ["critical_care"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@critical_care_books"},
        {"username": "anesthesia_books", "subscribers_estimate": 74233, "specialty_tags": ["anaesthesia"], "has_direct_ebooks": True, "source_url": "https://tgstat.com/channel/@anesthesia_books"},
    ],
}

if __name__ == "__main__":
    for name, items in BUNDLES.items():
        (DATA / name).write_text(json.dumps(items, indent=2), encoding="utf-8")
    print("Wrote", len(BUNDLES), "agent files")
