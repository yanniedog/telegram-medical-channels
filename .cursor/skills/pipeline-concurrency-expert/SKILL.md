---
name: pipeline-concurrency-expert
description: run_full_rerun, swarm 50+ workers, anti-throttle, env knobs.
---

# Pipeline concurrency expert

Paths: run_full_rerun.py, run_full_analysis.py, SWARM_RUNBOOK.md

Command: python run_full_rerun.py

Optional verify: npm run verify:local -- --full-rerun

Windows local only. Coordinates other experts via orchestrator for focused PRs.
