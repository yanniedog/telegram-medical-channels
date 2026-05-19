"""Expand channel list via Lyzem + merge into discovery cache."""
import json
import time
from pathlib import Path

import httpx

from discover_channels import QUERIES, fetch_channel_meta, scrape_lyzem_page

HEADERS = {"User-Agent": "Mozilla/5.0"}
MIN_SUBS = 2000
OUT = Path("data/discovered_channels.json")


def main():
    seen = set()
    if Path("channel_seeds.json").exists():
        seen.update(u.lower() for u in json.loads(Path("channel_seeds.json").read_text(encoding="utf-8")))
    if OUT.exists():
        raw = json.loads(OUT.read_text(encoding="utf-8"))
        seen.update(raw.get("all", {}).keys())
        seen.update(raw.get("qualified", {}).keys())

    extra_queries = [
        "medicina libros pdf", "kitap tıp", "livres médicaux", "medizin bücher",
        "libri medicina", "medical atlas pdf", "nursing books pdf", "dentistry books pdf",
        "pharmacy books pdf", "orthopedics books pdf", "cardiology books pdf",
        "medical kindle", "medbook pdf channel", "harrison medicine pdf",
    ]
    all_q = list(dict.fromkeys(QUERIES + extra_queries))

    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for q in all_q:
            for page in range(1, 16):
                for h in scrape_lyzem_page(client, q, page):
                    seen.add(h.lower())
                time.sleep(0.35)
            time.sleep(0.5)
        print("handles", len(seen))

        all_meta = {}
        if OUT.exists():
            all_meta = json.loads(OUT.read_text(encoding="utf-8")).get("all", {})

        for i, uname in enumerate(sorted(seen)):
            if uname in all_meta and (all_meta[uname].get("subscribers") or 0) >= MIN_SUBS:
                continue
            meta = fetch_channel_meta(client, uname)
            if not meta.get("error"):
                all_meta[uname] = meta
            if (i + 1) % 20 == 0:
                qn = sum(1 for v in all_meta.values() if (v.get("subscribers") or 0) >= MIN_SUBS)
                print(f"{i+1}/{len(seen)} qualified={qn}")
            time.sleep(0.28)

    qualified = {k: v for k, v in all_meta.items() if (v.get("subscribers") or 0) >= MIN_SUBS}
    OUT.write_text(
        json.dumps({"qualified": qualified, "all": all_meta}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("qualified", len(qualified), "all", len(all_meta))


if __name__ == "__main__":
    main()
