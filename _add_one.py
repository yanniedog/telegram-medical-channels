import json
from pathlib import Path
from health_relevance import health_relevance_score, has_books_pdfs_signal
p = Path("data/agent_swarm/swarm_radiology_pathology.json")
data = json.loads(p.read_text(encoding="utf-8"))
e = {"username": "medicalbooksstorea", "subscribers_estimate": 38372, "title": "Medical Books", "has_books_or_pdfs_in_name": True, "health_relevant": True, "possibly_health_relevant": False, "specialty_tags": ["pathology", "radiology", "microbiology", "biochemistry", "lab_medicine", "histology"], "notes": "Large free medical books channel (t.me May 2026); multi-specialty PDF library"}
data.append(e)
data = sorted({x["username"]: x for x in data}.values(), key=lambda x: (-x["subscribers_estimate"], x["username"]))
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(data))
