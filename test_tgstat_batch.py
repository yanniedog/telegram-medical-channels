from tgstat_scraper import scrape_tgstat_channel

for u in [
    "pdf4yo",
    "MedicalBooksStoress",
    "internal_medicine_material",
    "medical_ebook_pdfs",
    "radiologygoldenbooks",
    "Medical_Free_Ebooks",
]:
    p = scrape_tgstat_channel(u)
    print(u, len(p))
