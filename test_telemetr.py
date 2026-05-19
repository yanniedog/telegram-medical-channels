from telemetr_scraper import scrape_telemetr_channel

for u in ["medicalbooksstoress", "Million_medical_books", "pdf4yo"]:
    p = scrape_telemetr_channel(u)
    print(u, len(p))
    if p:
        print(" ", p[0].get("text", "")[:80])
