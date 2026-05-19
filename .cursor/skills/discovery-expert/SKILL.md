---
name: discovery-expert
description: Lyzem shards, swarm manifest, merge_agent_discoveries, channel_seeds, discovered_channels.json.
---

# Discovery expert

Paths: build_swarm_manifest.py, run_lyzem_shards.py, merge_swarm_shards.py, merge_agent_discoveries.py, channel_seeds.json, data/agent_swarm/, data/discovered_channels.json

Commands: python build_swarm_manifest.py ; python merge_swarm_shards.py ; python merge_agent_discoveries.py

See SWARM_RUNBOOK.md for wave spawns. Handoff to orchestrator for PR; scrape-expert after registry ready. No mock channels.
