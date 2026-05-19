import json
from discover_channels import fetch_channel_meta, parse_subscribers
import httpx

HEADERS = {"User-Agent": "Mozilla/5.0"}
with httpx.Client(headers=HEADERS, follow_redirects=True) as c:
    for u in ["Medbooksvn2", "MedicalBooksStoress", "Million_medical_books"]:
        m = fetch_channel_meta(c, u)
        print(u, "text=", m.get("subscribers_text"), "parsed=", parse_subscribers(m.get("subscribers_text")))
