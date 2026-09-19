# FixIQ — Project Overview

## What this is
FixIQ is a hackathon project: a multimodal AI agent system that acts as a persistent "digital doctor" for individual factory machines. It diagnoses faults from a photo + voice description, cross-references machine manuals and that specific machine's own repair history via RAG, predicts upcoming service needs, tracks machine health/efficiency, and auto-escalates unresolved issues to the right technician over Slack — logging the whole resolution conversation back into that machine's own memory so it gets smarter over time.

This is NOT a generic chatbot over documents. The core differentiator is **per-machine memory**: each machine has its own isolated knowledge base that accumulates its own fault/fix history, separate from every other machine, even ones of the same model.

## The problem (for judges)
Technicians on a factory floor lose significant time per fault event doing three separate lookups: flipping through PDF manuals, checking sensor logs for anomalies, and searching past tickets for "have we seen this before." That lag directly hits machine uptime — the core KPI in most Industry 4.0/5.0 hackathon tracks.

## Chosen industry vertical: Automotive manufacturing (robotics + precision machining)
We chose automotive manufacturing because it lets us legitimately combine three of the four candidate industries (automotive, aerospace, robotics, precision engineering) in one demoable line, using real, well-documented failure modes:
- 6-axis robotic welding arm → robotics
- CNC precision mill → precision engineering
- Conveyor/press station → general automotive
- Torque calibration station → ties directly into AS9100/IATF 16949 compliance narrative, which judges from a manufacturing background will recognize

## Core feature list (do not miss any of these)

1. **Mock machine fleet** — 4 machines, each with realistic simulated sensor streams (see `02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md`). No real hardware — everything is spoofed, but must not *feel* spoofed.
2. **Per-machine RAG memory** — each machine has its own vector DB collection for its ticket/repair history. Manuals are shared per *machine model*, not per instance. See `01_ARCHITECTURE.md`.
3. **Continual learning loop** — every resolved ticket (including full Slack thread) gets embedded back into that machine's own collection, so recurring faults get recognized and solved faster over time.
4. **Recurring fault detection** — cluster a machine's past incidents by embedding similarity + frequency, surface "this pattern has occurred N times, longest-lasting fix was X."
5. **Machine health scoring** — 0–100 score based on deviation from that machine's own historical baseline (not a generic threshold).
6. **Predictive service timing (RUL)** — trend-line extrapolation on a degrading sensor metric against a known failure threshold, explicitly labeled as heuristic/trend-based, not a trained ML model.
7. **Fleet dashboard** — OEE (Overall Equipment Effectiveness = Availability × Performance × Quality) per machine, health scores, predicted service windows, recurring-fault leaderboard, downtime log.
8. **Machine detail view** — live (simulated) sensor charts, health gauge, RUL estimate, failure history table (Problem → Cause → Remedy taxonomy), a chat window scoped to only that machine's memory.
9. **Multimodal resolver agent** — technician uploads a photo + voice note describing a symptom. Agent transcribes audio, analyzes the image for defect signatures, pulls the machine's live sensor snapshot, queries that machine's own RAG collection + the shared model manual, fuses everything into a ranked diagnosis with confidence + step-by-step repair instructions pulled from the actual manual.
10. **Escalation decision logic** — if confidence is high and severity is low, the agent shows guided self-resolve steps. If severity crosses a threshold or needs specialized skill, it auto-generates a structured work order and assigns it to the right technician from a small mock roster (tagged by specialty: mechanical / electrical / calibration).
11. **Slack integration** — escalations post to Slack (Bolt + Socket Mode, no public URL needed), open a thread, technician and bot converse in-thread, a "Mark Resolved" button closes the ticket. Full thread gets mirrored to the main website under that machine AND embedded into that machine's RAG collection.
12. **Hidden failure trigger modes** — 3 hidden modes (one per relevant machine) that can be secretly triggered during a live demo to gradually escalate a machine toward a realistic failure state, for demoing diagnosis + escalation live.
13. **Fully offline LLM stack** — the reasoning/vision/embedding/speech pipeline runs on a local quantized model (~3-4B params), NOT a cloud API, so judges can verify nothing is faked or calling out to GPT-4 behind the scenes. Slack itself requires internet — this is the one explicit exception and should be stated honestly to judges, not hidden.

## Standards/frameworks referenced (use these terms accurately in UI copy and pitch — they are real, not invented)
- **ISO 13374** — defines the condition-monitoring pipeline this system implements: Data Acquisition → Data Manipulation → State Detection → Health Assessment → Prognostic Assessment → Advisory Generation.
- **ISO 14224** — reliability/maintenance data collection standard (equipment data, failure data, maintenance data).
- **OEE (Overall Equipment Effectiveness)** — Availability × Performance × Quality — the real KPI this system's dashboard should be built around.
- **Problem → Cause → Remedy** — a real failure-code taxonomy structure used in manufacturing maintenance data governance; use this structure for the failure history table.
- **AS9100 / IATF 16949** — aerospace and automotive quality management standards; referenced for the torque-calibration-station machine's narrative (calibration drift is a real audit hotspot under AS9100).

## What "done" looks like for the hackathon demo
A judge should be able to:
1. See the fleet dashboard with 4 machines showing live-feeling sensor data, health scores, and OEE.
2. Open a machine's detail view and see its own chat history / fault history.
3. Trigger (or watch you trigger) one of the 3 hidden failure modes and watch the health score degrade in real time.
4. Upload a photo + voice note describing a symptom and get back a real diagnosis with confidence + repair steps pulled from an actual manual excerpt — generated by a genuinely local LLM, not a cloud call.
5. See the system auto-escalate to Slack, open a thread, and (optionally) watch a "technician" reply in Slack and see that conversation appear back on the website in real time.
6. Ask the same machine about a similar fault a second time and see the system reference its own past resolution — proving the per-machine learning loop is real, not a claim.

See the other files in this handoff for full technical detail:
- `01_ARCHITECTURE.md` — system architecture, data model, RAG design, resolver agent flow
- `02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md` — the 4 machines, fault modes, sensor generation math, hidden trigger modes
- `03_OFFLINE_LLM_AND_TECH_STACK.md` — local model choices, embeddings, speech-to-text, full tech stack
- `04_SLACK_INTEGRATION.md` — Slack Bolt architecture, threading, resolution flow
- `05_BUILD_PLAN_6_DAYS.md` — day-by-day build order
- `06_RESEARCH_AND_SOURCES.md` — every source, standard, and manual link used to ground this design
