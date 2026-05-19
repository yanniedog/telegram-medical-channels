---
name: data-registry-expert
description: channels_registry.json, normalize_data, rescrape_queue, dedupe.
---

# Data registry expert

Paths: normalize_data.py, channel_registry.py, data/channels_registry.json, data/rescrape_queue.json

Command: python normalize_data.py

Handoff: scrape-expert for queue; medical-relevance-expert for filters.
