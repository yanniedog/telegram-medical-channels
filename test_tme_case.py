from channel_scraper import scrape_channel

for u in ["MedicalBooksStoress", "pdf4yo", "Internal_medicine_material", "webofmedical"]:
    posts = scrape_channel(u, max_pages=5, delay=0.3)
    print(u, len(posts), posts[0].post_id if posts else None)
