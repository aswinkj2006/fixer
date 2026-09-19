# FixIQ — 6-Day Build Plan

Sequencing note: Days 3–5 all depend on Day 1's data model and sensor-spoofing generator being solid. Don't rush Day 1. If time runs short later, cut RUL polish first (label it heuristic and move on) — protect the continual-learning loop and recurring-fault detection, since those are what make "learns per machine" a demonstrable fact rather than a claim in the pitch.

## Day 1 — Foundation
- Seed the 4 mock machines (see `02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md`) and the full data model (`01_ARCHITECTURE.md` §2): machines, sensor_readings, tickets, ticket_messages, technicians, failure_codes.
- Build the sensor-spoofing script: Ornstein-Uhlenbeck baseline + duty-cycle layer per sensor type, with the 3 hidden anomaly-trigger presets wired in (even if not yet fully tuned).
- **Test local LLM inference speed on the actual dev laptop today** (`ollama pull gemma3:4b`, run one real image + text inference, time it). This determines pacing/architecture decisions for the rest of the build — do not defer this.
- Download and stage the manual sources from `06_RESEARCH_AND_SOURCES.md` (especially the FANUC ARC Mate manuals for M-01) for chunking on Day 2.

## Day 2 — RAG foundation
- Set up the vector DB (Chroma or FAISS) with the two-tier structure: shared per-model manual collections (Tier 1) and isolated per-machine-instance collections (Tier 2).
- Ingest the staged manuals into Tier 1, chunked appropriately.
- Set up `nomic-embed-text` for embeddings.
- Test retrieval scoping explicitly — confirm a query against M-01's Tier 2 collection never returns M-02's data, even if they were the same model.

## Day 3 — Resolver agent core
- Build the multimodal fusion pipeline (`03_OFFLINE_LLM_AND_TECH_STACK.md`): whisper.cpp transcription → vision model short defect summary → retrieval (Tier 1 + Tier 2 + live sensor snapshot) → reasoning model call → diagnosis + confidence + repair steps + severity, as JSON.
- Get one clean end-to-end run working manually (via script/CLI) before touching any UI.

## Day 4 — Learning loop + health/RUL
- Build the continual-learning hook: on ticket resolution, chunk and embed the full conversation into that machine's Tier 2 collection.
- Build recurring-fault detection: cluster a machine's own past incidents by embedding similarity + occurrence count.
- Build the health score (deviation from that machine's own historical baseline) and RUL heuristic (trend extrapolation to a failure threshold, clearly labeled as heuristic).
- Register the Slack app and get a basic `chat.postMessage` call working (get ahead of Day 5's Slack work).

## Day 5 — Dashboard, machine detail view, Slack, escalation
- Build the fleet dashboard: OEE per machine, health scores, predicted service windows, recurring-fault leaderboard, downtime log.
- Build the machine detail view: live sensor charts, health gauge, RUL estimate, Problem→Cause→Remedy failure history table, machine-scoped chat window.
- Build the full Slack integration per `04_SLACK_INTEGRATION.md`: threading, technician mention/routing, "Mark Resolved" button, real-time mirroring to `ticket_messages`.
- Wire the escalation decision node (`01_ARCHITECTURE.md` §5) to actually fire the Slack flow for high-severity cases.

## Day 6 — Integration, polish, demo rehearsal
- Full integration pass across all pieces.
- Rehearse the demo narrative in this order: (1) normal operation on the dashboard, (2) trigger a hidden failure mode and show the health score degrading live, (3) run the multimodal resolver agent on the fault and show diagnosis + repair steps pulled from a real manual excerpt, (4) show escalation firing to Slack and a thread opening, (5) resolve it and immediately ask the same machine about a similar fault again to demonstrate it retrieves its own past resolution.
- Buffer time for the inevitable last-day breakage — do not schedule new features on this day.
