import json
from pathlib import Path
from content_analyzer import is_link_only_channel_post

posts_dir = Path("data/posts")
for path in posts_dir.glob("*.json"):
    posts = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    for p in posts:
        old = p.get("is_link_only_channel_promo")
        new = is_link_only_channel_post(p)
        if old != new:
            p["is_link_only_channel_promo"] = new
            changed += 1
    if changed:
        path.write_text(json.dumps(posts, ensure_ascii=False, indent=2), encoding="utf-8")
        print(path.name, changed)
